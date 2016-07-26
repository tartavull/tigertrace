import networkx as nx
import struct 

from tigertrace.tasks.task import Task

class Export(Task):
  def __init__(self, sampler=None):
    pass

  def fetch(self, store, queue):
    g = nx.Graph()
    count = store.merges_count
    for k, v in store.get_all_from_table(store.MERGES_TABLE):
      weight, order = v
      # normalized_weight = (1.0 / count) * (count - order)      
      g.add_edge(*k, weight=weight)
    
    self.mst = nx.minimum_spanning_tree(g)
    
  def run(self):
    pass
 

  def save(self, store, queue):

    nodes = set(self.mst.nodes())
    b = bytearray()
    while len(nodes):
      element_from_nodes = next(iter(nodes))
      for i, edge in enumerate(nx.algorithms.traversal.bfs_edges(self.mst, element_from_nodes)):
        if edge[0] in nodes:
          nodes.remove(edge[0])
        if edge[1] in nodes:
          nodes.remove(edge[1])
        b.extend(struct.pack('<IIIIdd',i,edge[1], edge[0],0, self.mst[edge[0]][edge[1]]['weight'],0.0))

    #TODO add this method to dataset!
    with open(store.dataset_path+'/mst.data','wb') as f:
      f.write(b)