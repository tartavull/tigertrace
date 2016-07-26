import unittest

class TestStore(unittest.TestCase):

    def setUp(self):
        from tigertrace.stores.memory import MemoryStore
        self.store = MemoryStore('/tmp/store')

    def tearDown(self):
        del self.store

    def test_basic_put(self):
        self.store._put('hello', 'world')
        self.assertEqual(self.store._get('hello'),'world')

    def test_edge_store(self):
        """
          Check that the order of the id in the edge
          does not matter
        """
        val = {'somefeature':'somevalue'}
        self.store.put_edge(1,2, val)

        self.assertEqual(self.store.get_edge(1,2),val)
        self.assertEqual(self.store.get_edge(2,1),val)

        self.store.put_edge(4,2, val)
        self.assertEqual(self.store.get_edge(2,4),val)
        self.assertEqual(self.store.get_edge(4,2), val)

    def test_node_store(self):
        """
        Check if nodes are correctly inserted
        """
        self.store.put_node(1, {'node_features_1':1})
        self.assertEqual(self.store.get_node(1),{'node_features_1':1})

    def test_hash_length(self):
        """
        Keys are hashed when inserting into the store.
        Make sure the hashing is correct
        """
        self.assertEqual(self.store.make_hash(0, table=0, key_bits=8), b'\x00\x00')
        self.assertEqual(self.store.make_hash(255, table=0, key_bits=8), b'\x00\xff')
        self.assertEqual(self.store.make_hash(256**2-1, table=1, key_bits=16), b'\x01\xff\xff')
        self.assertEqual(self.store.make_hash(256**4-1, table=11, key_bits=32), b'\x0b\xff\xff\xff\xff')
        self.assertEqual(self.store.make_hash(256**4-1, table=255, key_bits=32), b'\xff\xff\xff\xff\xff')
        self.assertEqual(self.store.make_hash(256**8-1, table=0, key_bits=64), b'\x00\xff\xff\xff\xff\xff\xff\xff\xff')

    def test_dump_load(self):
        from tigertrace.stores.memory import MemoryStore
        store_1 =  MemoryStore('/tmp')
        store_1.put_node(1, {'node_features_1':1})
        store_1.dump()
        
        store_2 =  MemoryStore('/tmp')
        store_2.restore()
        self.assertEqual(store_1.latest_id, store_2.latest_id)
        self.assertEqual(store_1.db, store_2.db)
