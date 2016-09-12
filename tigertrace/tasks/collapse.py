from tigertrace.tasks.task import Agglomeration
from tigertrace.tasks.evaluate import Evaluate
from tigertrace.features import Tree, Neighbors

class Collapse(Agglomeration):
  def __init__(self, id_1, id_2, sampler=None):
    assert id_1 < id_2
    self.id_1 = id_1
    self.id_2 = id_2
    self.sampler = sampler

  def fetch(self, store, queue):
    """
    """
    self.node_1 = store.get_node(self.id_1)
    self.node_2 = store.get_node(self.id_2)
    self.edge = store.get_edge(self.id_1, self.id_2)
    self.new_id = store.get_new_id()

    store.log.append(self.edge['features'])

    #Remove them, because we will update them
    store.delete_node(self.id_1)
    store.delete_node(self.id_2)
    store.delete_edge(self.id_1, self.id_2)

  def run(self):
    self.compute_affected()
    self.create_new_node()

  def save(self, store, queue):
    self.log_merge(store)
    self.update_edges_to_neighbors(store, queue)
    store.put_node(self.new_id, self.new_node)
  
  def compute_affected(self):
    """
      It is possible that some of the neighbors don't exist anymore.
    """
    #id_1 and id_2 are going to be included here
    self.all_nodes = self.node_1['neighbors'].union(self.node_2['neighbors'])
    self.only_neighbors = self.all_nodes.difference(Neighbors([self.id_1,self.id_2]))

  def create_new_node(self):
    new_node = self.sum_nodes_features(self.node_1, self.node_2)
    new_node['neighbors'] = self.only_neighbors
    new_node['tree'] = Tree(self.new_id)
    new_node['tree'].insert_left_tree(self.node_1['tree'])
    new_node['tree'].insert_right_tree(self.node_2['tree'])
    self.new_node = new_node

  def log_merge(self, store):
    """
      We want to use this to produce an mst that can be use with omni
      Or to produce a segmentation after agglomeration is done
    """
    #get atomic edge given edge
    atomic_edge = self.edge['tree'].get_leaf()
    if 'weight' in self.edge:
      store.log_merge(atomic_edge[0], atomic_edge[1], self.edge['weight'])
    else:
      store.log_merge(atomic_edge[0], atomic_edge[1], 1.0)

  def create_new_edge(self, neighbor, tree, only_node_1, only_node_2, store, queue):

    if neighbor in only_node_1:
      new_edge = store.get_edge(self.id_1, neighbor)
      store.delete_edge(self.id_1,neighbor) #if an exception is rised we won't be able to recover
      queue.remove_task('Collapse', store.sort_edge(self.id_1, neighbor))
      tree.insert_left_tree(new_edge['tree'])
    elif neighbor in only_node_2:
      new_edge = store.get_edge(self.id_2,neighbor)
      store.delete_edge(self.id_2,neighbor)
      queue.remove_task('Collapse', store.sort_edge(self.id_2, neighbor))
      tree.insert_right_tree(new_edge['tree'])
    else: #is a neighbor of both edges
      edge_from_node_1 = store.get_edge(self.id_1,neighbor)
      edge_from_node_2 = store.get_edge(self.id_2,neighbor)
      new_edge = self.sun_edges_features(edge_from_node_1,edge_from_node_2)
      store.delete_edge(self.id_1,neighbor)
      store.delete_edge(self.id_2,neighbor)
      queue.remove_task('Collapse', store.sort_edge(self.id_1, neighbor))
      queue.remove_task('Collapse', store.sort_edge(self.id_2, neighbor))
      tree.insert_left_tree(edge_from_node_1['tree'])
      tree.insert_right_tree(edge_from_node_2['tree'])
      try:
        #TODO is max the right function ?
        new_edge['weight'] = max(edge_from_node_1['weight'],edge_from_node_2['weight'])
      except: 
        pass

    new_edge['tree'] = tree
    return new_edge

  def update_edges_to_neighbors(self, store, queue, threshold=0.1):
    """
      If under threshold we never consider it again for agglomeration
    """
    only_node_1 = self.node_1['neighbors'].difference(self.node_2['neighbors'])
    only_node_1.remove(self.id_2)
    only_node_2 = self.node_2['neighbors'].difference(self.node_1['neighbors'])
    only_node_2.remove(self.id_1)

    for neighbor_id in self.only_neighbors:
      neighbor_node = store.get_node(neighbor_id)
      assert neighbor_node is not None, "for some reason {} doesn't exists".format(neighbor_id) 

      neighbor_node['neighbors'] = neighbor_node['neighbors'].difference(Neighbors([self.id_1,self.id_2]))
      neighbor_node['neighbors'].add(self.new_id)
      store.put_node(neighbor_id, neighbor_node)
      new_edge_id = store.sort_edge(self.new_id, neighbor_id)
      tree = Tree(new_edge_id)
      new_edge = self.create_new_edge(neighbor_id, tree, only_node_1, only_node_2, store, queue)


      if (not 'weight' in new_edge or
          new_edge['weight'] > threshold):

        
        t = Evaluate(id_1=new_edge_id[0],id_2=new_edge_id[1],
                                  sampler=self.sampler)

        t.oracle = self.oracle
        t.classify = self.classify
        #the new node has a larger id that the neighbor
        t.node_1 = neighbor_node
        t.node_2 = self.new_node
        #We don't save this new edge
        #because it would have been deleted in the evaluate fetch method
        #which is not being called
        t.edge=new_edge
        t.run()
        t.save(store,queue)
      else:
        store.put_edge(new_edge_id[0],new_edge_id[1],new_edge)
