from collections import defaultdict
from itertools import product
import numpy as np
import cloudpickle

from tigertrace.tasks.task import Agglomeration
from tigertrace.features import Neighbors, Tree, SoftLabel

class Construct(Agglomeration):

  async = False

  def __init__(self, start, end, chunk_overlap, sampler=None):
    self.start = start
    self.end = end
    self.chunk_overlap = chunk_overlap

  def run(self):
    self.edges = defaultdict(lambda: {'aff': [], 'pos':[]} )
    self.nodes = defaultdict(lambda: {'soft_label': SoftLabel() , 'pos':[], 'semantic_sum':0 ,'neighbors':Neighbors()} )
    
    #Linear pass thru the array
    for z, y, x in product(*map(xrange,self.ml.shape)):
      ml_id = self.ml[z,y,x]
      if ml_id == 0: #ignore boundaries
        continue
      self.compute_edges(z,y,x, ml_id)
      self.compute_nodes(z,y,x, ml_id)

    #add neighbors to node
    #We needs this otherwise we would have to check all edges to find
    #the neighbors of a given node.
    for edge_id, edge in self.edges.items():
      self.nodes[edge_id[0]]['neighbors'].add(edge_id[1])
      self.nodes[edge_id[1]]['neighbors'].add(edge_id[0])
    
    if self.async:
      return cloudpickle.dumps(self.save)

  def compute_edges(self, z,y,x, ml_id):
    if z + 1 < self.ml.shape[0]:
      self.union_seg(ml_id, self.ml[z+1,y,x], 
                (z+0.5,y,x), 2)
    if y + 1 < self.ml.shape[1]:
      self.union_seg(ml_id, self.ml[z,y+1,x],
                (z,y+0.5,x), 1)
    if x + 1 < self.ml.shape[2]:
      self.union_seg(ml_id, self.ml[z,y,x+1],
                (z,y,x+0.5), 0,)

  def union_seg(self, id_1, id_2, voxel_position, axis):
    if id_1 == id_2 or id_2 == 0: #no need to check if id_0 == 0, because of run() for loop
      return 
    affinity = tuple( [axis] + list(np.ceil(np.asarray(voxel_position)).astype(int)))
    if id_1 > id_2:
      id_1 , id_2 = id_2, id_1

    if 'aff_sum' in self.edge_features or 'aff' in self.edge_features:
      self.edges[(id_1, id_2)]['aff'].append( self.aff[affinity] )

    if 'pos' in self.edge_features:
      self.edges[(id_1, id_2)]['pos'].append( np.asarray(voxel_position) )



  def compute_nodes(self, z,y,x, ml_id):
    if (z + self.chunk_overlap[0] < self.ml.shape[0] and
        y + self.chunk_overlap[1] < self.ml.shape[1] and
        x + self.chunk_overlap[2] < self.ml.shape[2]):
      self.nodes[ml_id]['pos'].append( np.array([z,y,x]) )
      if 'soft_label' in self.nodes_features and self.hl[z,y,x] != 0:
        self.nodes[ml_id]['soft_label'][self.hl[z,y,x]] += 1
      if 'semantic_sum' in self.nodes_features:
        self.nodes[ml_id]['semantic_sum'] += np.array(self.sl[:,z,y,x])
  
  def fetch(self, store, queue):
    self.ml = store.get_chunk(self.start, self.end,'machine_labels')
    if 'aff_sum' in self.edge_features:
      self.aff = store.get_chunk((0,)+self.start, (3,)+self.end,'affinities')
    if 'soft_label' in self.nodes_features:
      self.hl = store.get_chunk(self.start, self.end,'human_labels')
    if 'semantic_sum' in self.nodes_features:
      self.sl = store.get_chunk((0,)+self.start, (5,)+self.end,'machine_semantic_labels')

  def save_nodes_to_store(self, store, queue):
    for node_id, node in self.nodes.items():
      features = {}
      features['neighbors'] = node['neighbors']
      if 'soft_label' in self.nodes_features:
        features['soft_label'] = node['soft_label']
      if 'size' in self.nodes_features:
        features['size'] = len(node['pos'])
      if 'pos' in self.nodes_features:
        features['pos'] = np.asarray(node['pos'])
        if features['pos'].shape == (0,):
          features['pos'] = np.zeros(shape=(0,3))
      if 'mesh' in self.nodes_features:
        #Because ml incluedes the overlap is possible
        #That a node has a mesh in the overlap
        #But not a single voxel in the non-overlap region
        vertices, triangles = mesh.marche_cubes( node_id , self.ml )
        vertices += np.asarray(self.start).astype(np.uint16) * 2 #translate mesh
        features['mesh'] = mesh.get_adjacent( vertices, triangles )
      if 'semantic_sum' in self.nodes_features:
        features['semantic_sum'] = node['semantic_sum']

      features['tree'] = Tree(node_id)
      existent_node_features = store.get_node(node_id)
      if existent_node_features:
        features = self.sum_nodes_features(existent_node_features, features )
      store.put_node(node_id, features)

  def save_edges_to_store(self,store, queue):
    for edge_id, edge in self.edges.items():
      features = {}
      features['weight'] = None
      if 'aff' in self.edge_features:
        features['aff'] = np.asarray(edge['aff'])
      if 'aff_sum' in self.edge_features:
        features['aff_sum'] = np.sum(edge['aff'])
      if 'pos' in self.edge_features:
        features['pos'] = np.asarray(edge['pos'])
      if 'size' in self.edge_features:
        features['size'] = len(edge['aff'])
      if 'mesh' in self.edge_features and 'pos' in self.edge_features:
        features['mesh'] =  mesh.get_patch(edge_id[0],edge_id[1], features['pos'] , self.ml, translation=self.start)

      features['tree'] = Tree(edge_id)
      existent_edge_features = store.get_edge(*edge_id)
      if existent_edge_features:
        features = self.sun_edges_features(existent_edge_features, features)
        
      store.put_edge(edge_id[0], edge_id[1], features)
      queue.submit_new_task('Evaluate', edge_id)

  def save(self, store, queue):
    self.save_nodes_to_store(store, queue)
    self.save_edges_to_store(store, queue)
