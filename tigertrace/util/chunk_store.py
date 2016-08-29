import numpy as np
import lmdb
import shutil
from itertools import product
import leveldb

class LevelDBStore(object):
  """
  It does not allow multiprocessesing
  """
  def __init__(self, dataset_id= 0, dbfolder='/tmp/db', delete=False):
    self.db = leveldb.LevelDB(dbfolder)

  def _get(self, key):
    try:
      return self.db.Get(key)
    except KeyError:
      return None

  def _range_iter(self, key_from, key_to):
    return self.db.RangeIter(key_from, key_to)

  @profile
  def _put(self, key, value):
    self.db.Put(key, value)

  def _delete(self, key):
    self.db.Delete(key)

  def _drop_db(self):
    shutil.rmtree(self.dbfolder)

class ChunkStore(object):
  
  def __init__(self,chunk_size=(64,256,256)):
    self.chunk_size = chunk_size  
    self.dataset_size = [None,None,None]
    self.store = LevelDBStore()

  def _make_key(self, chunk_pos):
    return str(chunk_pos)

  def _floor_div(self, a ,b):
    return np.floor(a / float(b)).astype(int)

  def _ceil_div(self, a, b):
    return np.ceil(a / float(b)).astype(int)

  def _interval(self, _slice, chunk_size):
    for x in xrange(self._floor_div(_slice.start, chunk_size), self._ceil_div(_slice.stop, chunk_size)):
      yield x , max(_slice.start - x * chunk_size, 0) , min(_slice.stop - x* chunk_size, chunk_size), max(_slice.start , x * chunk_size) , min(_slice.stop ,  (x+1) * chunk_size)

  
  @profile
  def _update_chunk(self, chunk_pos, x_min, x_max, y_min, y_max, z_min, z_max, values):
    chunk = self.store._get(str(chunk_pos))
    if chunk is None:
      chunk = np.zeros(shape=self.chunk_size)
    else:
      chunk = np.fromstring(chunk).reshape(*self.chunk_size)

    chunk[x_min:x_max, y_min:y_max, z_min:z_max] = values
    serialized = chunk.tostring()
    self.store._put(self._make_key(chunk_pos), serialized)

  
  def _check_size(self, slices, item ):

    fixed = list(slices)
    for axis, _slice in enumerate(slices):
      if _slice.start is None and _slice.stop is None:
        print axis, _slice
        if self.dataset_size[axis] is None:
          self.dataset_size[axis] = item.shape[axis]
          fixed[axis] = slice(0, item.shape[axis])
        else:
          self.dataset_size[axis] = self.dataset_size[axis]
          fixed[axis] = slice(0, self.dataset_size[axis])
      else:
        self.dataset_size[axis] = max(self.dataset_size[axis], _slice.stop)
    return fixed

  def __setitem__(self, key, item):
    slices = self._check_size( key, item)
    print slices
    for (x_pos, rel_min_x, rel_max_x, 
                 abs_min_x, abs_max_x)  in self._interval(slices[0], self.chunk_size[0]):
      for (y_pos, rel_min_y, rel_max_y, 
                   abs_min_y, abs_max_y) in self._interval(slices[1], self.chunk_size[1]):
        for (z_pos, rel_min_z, rel_max_z, 
                     abs_min_z, abs_max_z)  in self._interval(slices[2], self.chunk_size[2]):

          self._update_chunk((x_pos, y_pos, z_pos),
            rel_min_x, rel_max_x,
            rel_min_y, rel_max_y,
            rel_min_z, rel_max_z,
            item[abs_min_x:abs_max_x,
                 abs_min_y:abs_max_y,
                 abs_min_z:abs_max_z])

  @profile
  def __getitem__(self, key):
    
    start = tuple(k.start for k in key)
    shape = tuple(k.stop - k.start for k in key)
    array = np.zeros(shape=shape)
    for (x_pos, rel_min_x, rel_max_x, 
                 abs_min_x, abs_max_x)  in self._interval(key[0], self.chunk_size[0]):
      for (y_pos, rel_min_y, rel_max_y, 
                   abs_min_y, abs_max_y) in self._interval(key[1], self.chunk_size[1]):
        for (z_pos, rel_min_z, rel_max_z, 
                     abs_min_z, abs_max_z)  in self._interval(key[2], self.chunk_size[2]):  
          
          chunk_pos = (x_pos, y_pos, z_pos)
          chunk = self.store._get(self._make_key(chunk_pos))
          chunk = np.fromstring(chunk).reshape(*self.chunk_size)
          array[rel_min_x - start[0]:rel_max_x - start[0],
                rel_min_y - start[1]:rel_max_y - start[1],
                rel_min_z - start[2]:rel_max_z - start[2]
                ] = chunk[rel_min_x:rel_max_x,
                          rel_min_y:rel_max_y,
                          rel_min_z:rel_max_z]

    return array

@profile
def test():
  # s = ChunkStore()
  # s[0:5,0:5,0:5] = np.ones(shape=(6,6,6))
  # s[0:5,0:5,0:5] = np.zeros(shape=(6,6,6))

  # print s[0:5,0:5,0:5]

  # result = s[0:6,0:6,0:6]
  # np.all(result == np.ones(shape=(6,6,6)))

  import h5py
  with h5py.File('/home/it2/small_piriform/machine_labels.h5') as f:
    s = ChunkStore()
    item = f['main'][:]
    s[:,:,:] = item
    a = s[0:64,0:256,0:256]
    f.create_dataset('copy',data=a)


if __name__ == '__main__':
  test()
  