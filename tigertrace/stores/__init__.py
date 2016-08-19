import logging
import h5py
import struct
from six.moves import cPickle as pickle
import numpy as np

class Store(object):
  IMAGES_TABLE = 0
  NODE_TABLE = 1
  EDGE_TABLE = 2
  MERGES_TABLE = 3
  OPERATIONS_TABLE = 4

  def __init__(self, dataset_path, delete=False):
    self.dataset_path = dataset_path
    self.dbfolder = self.dataset_path + '/store'
    self.delete = delete
    self.latest_id = 0
    self.db = self._init_db()
    self.log = []

    #count merges
    self.merges_count = 0
    #dump triplets
    self.ops = []
    self.batch = 0

  def make_hash(self, *keys, **kwargs):
    """
    No padding in the hash, that's why we are using '<'
    """
    key_bits= kwargs.get('key_bits', 32)
    table = kwargs.get('table')
    code = {8:'B',16:'H',32:'I',64:'Q'}[key_bits]
    return struct.pack('<B{}'.format(code*len(keys)), table, *keys)

  def _unhash(self, string , **kwargs):
    key_bits= kwargs.get('key_bits', 32)
    keys = kwargs.get('keys',2)
    code = {8:'B',16:'H',32:'I',64:'Q'}[key_bits]
    return struct.unpack('<B{}'.format(code*keys),string)[1:]

  def get_new_id(self):
    self.latest_id += 1
    return self.latest_id

  def sort_edge(self, edge_src, edge_dst):
    """
    Edge src should always be smaller that dst
    """
    if edge_src > edge_dst:
        return edge_dst, edge_src
    else:
      return edge_src, edge_dst

  def put_edge(self, edge_src, edge_dst , features, update=True):
    """
      No 2 processes can be writting the same edge at the same time
      because it has to first lock the nodes related to the edge
    """
    #TODO if exists update provided features included
 
    key = self.make_hash(*self.sort_edge(edge_src, edge_dst), table=self.EDGE_TABLE)
    # self._put( key , njson.serialize_features(features))
    self._put( key , features)


  def get_edge(self, edge_src, edge_dst, features_to_get=None):
    key = self.make_hash(*self.sort_edge(edge_src, edge_dst), table=self.EDGE_TABLE)
    return self._get(key) #return the features

  def put_node(self, node_id, features , update=False):
    key = self.make_hash(node_id, table=self.NODE_TABLE)
    self._put( key , features)
    self.latest_id = max(self.latest_id, node_id)
   
  def get_node(self, node_id, features_to_get=None):
    key = self.make_hash(node_id, table=self.NODE_TABLE)
    return self._get(key) #return the features

  def delete_node(self, node_id):
    key = self.make_hash(node_id,table=self.NODE_TABLE)
    self._delete(key)
    
  def delete_edge(self, edge_src, edge_dst):
    key = self.make_hash(*self.sort_edge(edge_src, edge_dst),table=self.EDGE_TABLE)
    self._delete(key)

  def log_merge(self, edge_src, edge_dst, weight):
    key = self.make_hash(*self.sort_edge(edge_src, edge_dst), table=self.MERGES_TABLE)
    self.merges_count += 1 
    self._put( key , (weight, self.merges_count ))

  def log_operation(self, edge_src, edge_dst, operation):
    self.ops.append(operation)
    if len(self.ops) %1000 == 0:
      with open('{}/triplets/{:06d}.p'.format(self.dataset_path,self.batch),'wb') as f:
        logging.debug('saving to disk')
        pickle.dump(self.ops,f)
        self.ops = []
        self.batch += 1

  def get_all_from_table(self, table):
    key_from = self.make_hash(0, 0, table=table)
    max_value = np.iinfo(np.uint32).max
    key_to = self.make_hash(max_value, max_value, table=table)
    for k, v in self._range_iter(key_from,key_to):
      yield self._unhash(k),v

  def get_all_sorted_operations(self):
    key_from = self.make_hash(0, 0, table=self.OPERATIONS_TABLE)
    max_value = np.iinfo(np.uint32).max
    key_to = self.make_hash(max_value, max_value, table=self.OPERATIONS_TABLE)
    operations = []
    for k, v in self._range_iter(key_from,key_to):
      operations.append(v)
    return sorted(operations, key= lambda operation: operation['timestamp'])


  def get_dataset_shape(self):
    with h5py.File('{}/{}.h5'.format(self.dataset_path, 'machine_labels')) as f:
        return f['main'].shape

  def get_chunk(self, start, end, layer_type):
    with h5py.File('{}/{}.h5'.format(self.dataset_path, layer_type),'r') as f:
        slices =  [slice(s,e) for s,e in zip(start,end)]
        return f['main'][tuple(slices)]

  def __del__(self):
    #save to disk if is a fraction of 1000
    with open('{}/triplets/{:06d}.p'.format(self.dataset_path,self.batch),'wb') as f:
        logging.debug('saving to disk')
        pickle.dump(self.ops,f)

    with open('{}/log.p'.format(self.dataset_path),'wb') as f:
      pickle.dump(self.log,f)


    if self.delete:
      self._drop_db()