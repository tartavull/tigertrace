import numpy as np

from tigertrace.tasks.task import Agglomeration
from tigertrace.tasks.train import classifier
from tigertrace.features import SoftLabel

class Evaluate(Agglomeration):
  """
  This tasks computes the likelyhood that the two
  nodes connected by this edge belongs to the same object
  """
  def __init__(self, id_1, id_2, sampler, collapse_threshold=0.2):
    self.id_1 = id_1
    self.id_2 = id_2
    self.sampler = sampler
    self.collapse_threshold = collapse_threshold

  def fetch(self, store, queue):
    self.node_1 = store.get_node(self.id_1)
    self.node_2 = store.get_node(self.id_2)
    self.edge = store.get_edge(self.id_1, self.id_2)
    if (not self.node_1 
        or not self.node_2 
        or not self.edge):
      raise LookupError('Failed to compute triplet, because one of the nodes does not exist anymore')
  
  def run(self):
    self.features = self.compute_features()
    self.edge['weight'] = self.compute_weight(self.features)
  def add_soft_label(self, features):
    
    features['soft_label'] =  SoftLabel.triplet_feature(
          self.node_1['soft_label'],
          self.node_2['soft_label']) /  float(self.node_1['size'] * self.node_2['size'])

  def add_affinities(self, features):
    features['mean_affinity'] = np.mean(self.edge['aff'])
    features['max_affinity'] = np.max(self.edge['aff'])
    features['min_affinity'] = np.min(self.edge['aff'])
    features['median_affinity'] = np.median(self.edge['aff'])
    #TODO another histogram gaussianly blurred
    hist , _ = np.histogram(self.edge['aff'], bins=10,range=(0.0,1.0), density=True)
    for b , value in enumerate(hist):
      features['hist_bin_{}'.format(b)] = value

  def add_mean_affinity(self, features):
    features['mean_affinity'] = self.edge['aff_sum'] / self.edge['size']

  def add_sizes(self, features):
    features['edge_size'] = self.edge['size']
    features['size_1'] = self.node_1['size']
    features['size_2'] = self.node_2['size']

  def add_autoencoder(self, features):
    features['node_1_pos'] = self.node_1['pos']
    features['node_2_pos'] = self.node_2['pos']
    features['edge_pos'] = self.edge['pos']

    return

    node_1_arr, node_2_arr = self.create_boolean_array() 
    img1, img2 = self.sampler.images(node_1_arr, node_2_arr)
    features['autoencoder_1'] = np.sum(img1 * img2)**2/(np.sum(img1**2)*np.sum(img2**2))
    features['autoencoder_2'] = np.sum(img1 * img2)/np.sum(img1**2)
    features['autoencoder_3'] = np.sum(img2 * img1)/np.sum(img2**2)
    features['autoencoder_4'] = np.sum(img1 * img2)

  def add_mesh(self, features):
    #TODO verify this features work for the case that one objects resides inside the other
    #like an organel 
    disp_1, disp_2 = mesh.compute_feature( self.edge['mesh'] , self.node_1['mesh'] , self.node_2['mesh'])
    features['displacements_1'] = disp_1 #TODO this seems to be nan
    features['displacements_2'] = disp_2 #TODOthis seems to be nan
    features['size_edge_mesh'] = len(self.edge['mesh'])
    features['size_node_1_mesh'] = len(self.node_1['mesh'])
    features['size_node_2_mesh'] = len(self.node_2['mesh'])
    features['relative_mesh_size_1'] = len(self.edge['mesh'])/float(len(self.node_1['mesh']))
    features['relative_mesh_size_2'] = len(self.edge['mesh'])/float(len(self.node_2['mesh'])) 
    features['relative_mesh_size_3'] = len(self.node_1['mesh'])/float(len(self.node_2['mesh']))
    features['relative_mesh_size_4'] = len(self.node_2['mesh'])/float(len(self.node_1['mesh']))

  def add_semantic(self, features):
    features['semantic_sum'] = np.sum(self.node_1['semantic_sum'] * self.node_2['semantic_sum'] / (self.node_1['size'] * self.node_2['size']))

  def compute_features(self):
    
    features = {}
    if 'soft_label' in self.nodes_features and 'size' in self.nodes_features:
      self.add_soft_label(features)
    if 'aff' in self.edge_features:
      self.add_affinities(features)
    if 'aff_sum' in self.edge_features and 'size' in self.edge_features:
      #Optimized for speed
      self.add_mean_affinity(features)
    if 'size' in self.edge_features and 'size' in self.nodes_features:
      self.add_sizes(features)
    if 'pos' in self.nodes_features and 'pos' in self.edge_features:
      self.add_autoencoder(features)
    if 'mesh' in self.nodes_features and 'mesh' in self.edge_features:
      self.add_mesh(features)
    if 'semantic_sum'in self.nodes_features:
      self.add_semantic(features) 

    #Add the trees of both nodes, so that we can used them to run the autoencoder
    if 'tree'  in self.nodes_features:
      features['tree_1'] = self.node_1['tree']
      features['tree_2'] = self.node_2['tree']
    return features

  def compute_weight(self, features):
    if self.oracle:
      if features['soft_label'] >= 0.9:
        return features['mean_affinity']
      else:
        return 0.0
    else:
      return features['soft_label']
      return self.classify(features)

  def find_points_inside_box(self, positions, bbox_min, bbox_max, shape ):
    arr = np.zeros(shape=shape)
    for pos in positions:
      if np.all(bbox_min <= pos) and np.all(pos < bbox_max):
        arr[tuple(pos-bbox_min)] = 1
    return arr

  def create_boolean_array(self, z_size=32 , y_size=158, x_size=158 ):
    """This method 
    
    Args:
        node_1_pos (TYPE): sparse array of voxels postions
        node_2_pos (TYPE): sparse array of voxels postions
        e_pos (TYPE): sparse array of voxels postions
        x_size (int, optional): size of array
        y_size (int, optional): size of array
        z_size (int, optional): size of array
    
    Returns:
        tuple: both boolean arrays
    """
    #Find the center of mass of the contact region
    center = np.mean(np.asarray(self.edge['pos']), axis=0)
    bbox_max = np.array([center[0] + z_size/2, center[1] + y_size/2, center[2] + x_size/2])
    bbox_min = np.array([center[0] - z_size/2, center[1] - y_size/2, center[2] - x_size/2])
    
    shape=(z_size, y_size, x_size)
    node_1_arr = self.find_points_inside_box(self.node_1['pos'], bbox_min, bbox_max, shape)
    node_2_arr = self.find_points_inside_box(self.node_2['pos'], bbox_min, bbox_max, shape)

    return node_1_arr, node_2_arr

  def save(self, store, queue):
    if self.oracle:
      store.log_operation(self.id_1, self.id_2, self.features)

    self.edge['soft_label'] = self.features['soft_label']
    store.put_edge(self.id_1, self.id_2, self.edge)
    if self.edge['weight'] > self.collapse_threshold:
      queue.submit_new_task('Collapse', (self.id_1, self.id_2), priority=self.edge['weight'])