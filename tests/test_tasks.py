import unittest

import numpy as np

class TestIngest(unittest.TestCase):

	def setUp(self):
		from tigertrace.stores.memory import MemoryStore
		self.store = MemoryStore('/tmp/dataset')

		from tigertrace.queues import LocalQueue
		self.queue = LocalQueue('/tmp/dataset')

	def tearDown(self):
		del self.store
		del self.queue

	def test_multiple(self):
		import numpy as np
		from tigertrace.tasks import Ingest
		t = Ingest()
		t.chunk_size = np.array([10,10,10])
		t.shape = np.array([20,20,20])
		t.run()
		t.save(self.store, self.queue)
		self.assertEqual(len(self.queue),8)

	def test_dataset_smaller_than_chunk(self):
		import numpy as np
		from tigertrace.tasks import Ingest
		t = Ingest()
		t.chunk_size = np.array([20,20,20])
		t.shape = np.array([10,10,10])
		t.run()
		t.save(self.store, self.queue)
		self.assertEqual(len(self.queue),1)
		task_args = self.queue.q[0][1][1]
		self.assertEqual(task_args, ((0, 0, 0), (10, 10, 10), (0, 0, 0)))


class TestExport(unittest.TestCase):

	def setUp(self):
		from tigertrace.stores.memory import MemoryStore
		self.store = MemoryStore('/tmp')

		from tigertrace.queues import LocalQueue
		self.queue = LocalQueue('/tmp')

		from tigertrace.features import Tree, Neighbors, SoftLabel
		self.store.put_node(1, {'soft_label':SoftLabel({1:1}), 'size':10, 'neighbors':Neighbors([2,3,4]), 'tree':Tree(fromarray=[1])})
		self.store.put_node(2, {'soft_label':SoftLabel({1:1}), 'size':20, 'neighbors':Neighbors([1,3,4]), 'tree':Tree(fromarray=[2])})
		self.store.put_node(3, {'soft_label':SoftLabel({1:1}), 'size':30, 'neighbors':Neighbors([1,2,4]), 'tree':Tree(fromarray=[3])})
		self.store.put_node(4, {'soft_label':SoftLabel({1:1}), 'size':40, 'neighbors':Neighbors([1,2,3]), 'tree':Tree(fromarray=[4])})

		self.store.put_edge(1,2, {'aff_sum':1.0 , 'size':1.0, 'tree':Tree(fromarray=[(1,2)])})
		self.store.put_edge(1,3, {'aff_sum':0.9 , 'size':1.0, 'tree':Tree(fromarray=[(1,3)])})
		self.store.put_edge(1,4, {'aff_sum':0.8 , 'size':1.0, 'tree':Tree(fromarray=[(1,4)])})
		self.store.put_edge(2,3, {'aff_sum':0.91 , 'size':1.0, 'tree':Tree(fromarray=[(2,3)])})
		self.store.put_edge(2,4, {'aff_sum':0.91 , 'size':1.0, 'tree':Tree(fromarray=[(2,4)])})
		self.store.put_edge(3,4, {'aff_sum':0.95 , 'size':1.0, 'tree':Tree(fromarray=[(3,4)])})

	def test_correct_number_of_edges(self):
		"""
		Create a clique consting of 4 nodes (1,2,3,4)
		First merge 1-2 and then 3,4 and lastly 2-3
		And make sure mst looks correctly
		"""
		from tigertrace.tasks.task import Agglomeration
		from tigertrace.tasks.collapse import Collapse

		Agglomeration.nodes_features = ['tree','neighbors','size','soft_label']
		Agglomeration.edge_features = ['tree','aff_sum','size']
		Agglomeration.oracle = True
		t = Collapse(1,2, None)
		t.classify = None
		t.fetch(self.store, self.queue)
		t.run()
		t.save(self.store, self.queue)

		t = Collapse(3,4, None)
		t.classify = None
		t.fetch(self.store, self.queue)
		t.run()
		t.save(self.store, self.queue)

		#the node 1-2 will have an id of 5
		#and the node 3-4 an id of 6
		t = Collapse(5,6, None)
		t.classify = None
		t.fetch(self.store, self.queue)
		t.run()
		t.save(self.store, self.queue)

		#Because all edges are deleted after a merge, there is nothing left
		self.assertEqual(list(self.store.get_all_from_table(self.store.EDGE_TABLE)),[])
		self.assertEqual(len(list(self.store.get_all_from_table(self.store.MERGES_TABLE))),3)

		from tigertrace.tasks.export import Export
		t = Export()
		t.fetch(self.store, self.queue)
		t.save(self.store, self.queue)


class TestConstruct(unittest.TestCase):

	def setUp(self):
		from tigertrace.stores.memory import MemoryStore
		self.store = MemoryStore('/tmp')

		from tigertrace.queues import LocalQueue
		self.queue = LocalQueue('/tmp')

	def test_affinities_order(self):
		from tigertrace.tasks.construct import Construct
		import h5py
		"""
		Create a fake array of affinities and machine labels
		and make sure that the affinity sum has the correct values
		"""
		aff = np.array([np.nan, .12,  #x affinities
										np.nan, .34,	#x affinities
										np.nan, .56,	#x affinities
										np.nan, .78,	#x affinities

										np.nan, np.nan, #y affinities
										.13, .24,				#y affinities
										np.nan, np.nan, #y affinities
										.57, .68,				#y affinities

										np.nan, np.nan, #z affinities
										np.nan, np.nan,	#z affinities
										.15,.26,				#z affinities
										.37,.48					#z affinities
										],dtype=np.float32).reshape(3,2,2,2)
		with h5py.File('/tmp/affinities.h5','w') as f:
			f.create_dataset('main',data=aff)

		machine_labels = np.array([1,2,
															 3,4,
															 
															 5,6,
															 7,8], dtype=np.uint32).reshape(2,2,2)
		with h5py.File('/tmp/machine_labels.h5','w') as f:
			f.create_dataset('main',data=machine_labels) 


		t = Construct(start=(0,0,0),
									end=(2,2,2),
									chunk_overlap=(0,0,0))

		t.edge_features = ['tree','src','dst','size','aff_sum']
 	 	t.nodes_features = ['tree','neighbors','size']
 	 	t.fetch(self.store, self.queue)
 	 	t.run()
 	 	t.save(self.store, self.queue)

 	 	#There should be only 12 edges (the number of values different to NaN)
 	 	self.assertEqual(len(list(self.store.get_all_from_table(self.store.EDGE_TABLE))),12)

 	 	#All the edges should have the correct values
 	 	self.assertEqual(self.store.get_edge(1,2)['aff_sum'], np.float32(0.12))
 	 	self.assertEqual(self.store.get_edge(1,3)['aff_sum'], np.float32(0.13))
 	 	self.assertEqual(self.store.get_edge(1,5)['aff_sum'], np.float32(0.15))

 	 	self.assertEqual(self.store.get_edge(2,4)['aff_sum'], np.float32(0.24))
 	 	self.assertEqual(self.store.get_edge(2,6)['aff_sum'], np.float32(0.26))
 	 	
	 	self.assertEqual(self.store.get_edge(3,4)['aff_sum'], np.float32(0.34))
 	 	self.assertEqual(self.store.get_edge(3,7)['aff_sum'], np.float32(0.37))

 	 	self.assertEqual(self.store.get_edge(4,8)['aff_sum'], np.float32(0.48))


 	 	self.assertEqual(self.store.get_edge(5,6)['aff_sum'], np.float32(0.56))
 	 	self.assertEqual(self.store.get_edge(5,7)['aff_sum'], np.float32(0.57))

 	 	self.assertEqual(self.store.get_edge(6,8)['aff_sum'], np.float32(0.68))

 	 	self.assertEqual(self.store.get_edge(7,8)['aff_sum'], np.float32(0.78))


