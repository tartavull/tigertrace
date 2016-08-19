import numpy as np
import lmdb

from itertools import product
class Store(object):
  def __init__(self,  dbfolder='/tmp/db', delete=False):
    self.db = lmdb.Environment(path=dbfolder,map_size=1024**4)

  def _get(self, key):
    with self.db.begin() as txn:
      return txn.get(key)

  def _range_iter(self, key_from, key_to):
    with self.db.begin() as txn:
      cursor = txn.cursor()
      if cursor.set_range(key_from):
        for key, value in cursor:
          if key < key_to:
            yield key, 
      cursor.close()
      raise StopIteration

  def _put(self, key, value):
    with self.db.begin(write=True) as txn:
      txn.put(key, value)

  def _delete(self, key):
    with self.db.begin(write=True) as txn:
      txn.delete(key)

  def _drop_db(self):
    with env.begin(write=True) as txn:
      txn.drop(delete=True)

class ChunkStore(object):
  
  def __init__(self,chunk_size=(10,10,10)):
    self.chunk_size = chunk_size  
    self.dataset_size = (0,0,0)
    self.store = Store()

  def _floor_div(self, a ,b):
    return np.floor(a / float(b)).astype(int)

  def _ceil_div(self, a, b):
    return np.ceil(a / float(b)).astype(int)

  def _interval(self, _slice, chunk_size):
    for x in xrange(self._floor_div(_slice.start, chunk_size), self._ceil_div(_slice.stop, chunk_size)):
      yield x , max(_slice.start - x * chunk_size, 0) , min(_slice.stop - x* chunk_size, chunk_size), max(_slice.start , x * chunk_size) , min(_slice.stop ,  (x+1) * chunk_size)

  def _update_chunk(self, chunk_pos, x_min, x_max, y_min, y_max, z_min, z_max, values):
    chunk = self.store._get(str(chunk_pos))
    if chunk is None:
      chunk = np.zeros(shape=self.chunk_size)
    else:
      chunk = np.fromstring(chunk).reshape(*self.chunk_size)

    chunk[x_min:x_max, y_min:y_max, z_min:z_max] = values
    self.store._put(str(chunk_pos), chunk.tostring())

  def __setitem__(self, key, item):
    self.dataset_size = tuple(k.stop for k in key)
    for x_chunk, rel_chunk_min_x, rel_chunk_max_x, abs_chunk_min_x, abs_chunk_max_x  in self._interval(key[0], self.chunk_size[0]):
      for y_chunk, rel_chunk_min_y, rel_chunk_max_y, abs_chunk_min_y, abs_chunk_max_y in self._interval(key[1], self.chunk_size[1]):
        for z_chunk, rel_chunk_min_z, rel_chunk_max_z, abs_chunk_min_z, abs_chunk_max_z  in self._interval(key[2], self.chunk_size[2]):

          self._update_chunk((x_chunk, y_chunk, z_chunk),
            rel_chunk_min_x, rel_chunk_max_x,
            rel_chunk_min_y, rel_chunk_max_y,
            rel_chunk_min_z, rel_chunk_max_z,
            item[abs_chunk_min_x:abs_chunk_max_x,
                 abs_chunk_min_y:abs_chunk_max_y,
                 abs_chunk_min_z:abs_chunk_max_z])

  def __getitem__(self, key):
    
    start = tuple(k.start for k in key)
    shape = tuple(k.stop - k.start for k in key)
    array = np.zeros(shape=shape)
    for x_chunk, rel_chunk_min_x, rel_chunk_max_x, abs_chunk_min_x, abs_chunk_max_x  in self._interval(key[0], self.chunk_size[0]):
      for y_chunk, rel_chunk_min_y, rel_chunk_max_y, abs_chunk_min_y, abs_chunk_max_y in self._interval(key[1], self.chunk_size[1]):
        for z_chunk, rel_chunk_min_z, rel_chunk_max_z, abs_chunk_min_z, abs_chunk_max_z  in self._interval(key[2], self.chunk_size[2]):
          
          chunk_pos = (x_chunk, y_chunk, z_chunk)
          chunk = self.store._get(str(chunk_pos))
          chunk = np.fromstring(chunk).reshape(*self.chunk_size)
          array[rel_chunk_min_x - start[0]:rel_chunk_max_x - start[0],
                rel_chunk_min_y - start[1]:rel_chunk_max_y - start[1],
                rel_chunk_min_z - start[2]:rel_chunk_max_z - start[2]
                ] = chunk[rel_chunk_min_x:rel_chunk_max_x,
                          rel_chunk_min_y:rel_chunk_max_y,
                          rel_chunk_min_z:rel_chunk_max_z]

    return array

if __name__ == '__main__':
  
  s = ChunkStore()
  s[0:5,0:5,0:5] = np.ones(shape=(6,6,6))
  s[0:5,0:5,0:5] = np.ones(shape=(6,6,6))

  result = s[0:6,0:6,0:6]
  np.all(result == np.ones(shape=(6,6,6)))
