from six.moves import cPickle as pickle
from tigertrace.stores import Store

class MemoryStore(Store):
  """
    It is volatile
  """
  def __init__(self,dataset_path, delete=False):
    Store.__init__(self, dataset_path, delete)

  def _init_db(self):
    return dict()

  def _get(self, key):
    try:
      return self.db.get(key)
    except KeyError:
      return None

  def _range_iter(self, key_from, key_to):
    """It doesn't guarantee order"""
    for key, value in self.db.items():
      if key_from <= key < key_to:
        yield key, value
  
  def _put(self, key, value):
    self.db[key] = value

  def _delete(self, key):
    del self.db[key]

  def _drop_db(self):
    del self.db

  def dump(self):
    with open(self.dbfolder,'wb') as f:
      pickle.dump((self.db, self.latest_id), f)

  def restore(self):
    with open(self.dbfolder,'rb') as f:
      self.db, self.latest_id  = pickle.load(f)
