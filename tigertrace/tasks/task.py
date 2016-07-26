from copy import deepcopy


class Task(object):
    """General Task class, which can be used no only to agglomerate
     but not shutdown the cluster or do anything else.
    """
    async = False
    def fetch(self):
        """
        Does all the requests required before running.
        """
        pass

    def run(self):
        """
        Main execution code of the task.
        This task can be chose to be run in parallel
        """
        pass

    def save(self):
        """
        Does all the requests required after running.
        This shouldn't not be run in parallel
        """
        pass



class Agglomeration(Task):

  """Inherits Task and add methods useful for
     performing agglomeration on a graph 
  """
  oracle = False
  edge_features = ['tree','src','dst','size','aff_sum']
  nodes_features = ['tree','neighbors','size','soft_label','semantic_sum']

  def sum_nodes_features(self, f_1, f_2):
    """
       This method is used to sum the features when a node was part of two chunks,
       or when performing agglomeration and collapsing edges

       In the former case, both trees are identical.
       In the second case, the tree is updated later while collapsing the tree
    """

    features = {}
    for nf in self.nodes_features:
      features[nf] =  f_1[nf] + f_2[nf]

    if 'mesh' in self.nodes_features:
      features['mesh'] = mesh.merge_adjacents(f_1['mesh'], f_2['mesh'])
    
    return features

  def sun_edges_features(self, f_1, f_2):
    features = {}
    features['tree'] = f_1['tree']
    if 'aff' in self.edge_features:
      features['aff'] = np.concatenate([f_1['aff'],f_2['aff']])
    if 'aff_sum' in self.edge_features:
      features['aff_sum'] = f_1['aff_sum'] + f_2['aff_sum']
    if 'size' in self.edge_features:
      features['size'] = f_1['size'] + f_2['size']
    if 'pos' in self.edge_features:
      features['pos']= np.concatenate([f_1['pos'],f_2['pos']])
    if 'mesh' in self.edge_features: 
      features['mesh'] = mesh.merge_adjacents(f_1['mesh'], f_2['mesh'])
    return features