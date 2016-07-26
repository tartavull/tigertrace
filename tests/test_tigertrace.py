#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_tigertrace
----------------------------------

Tests for `tigertrace` module.
"""


from __future__ import print_function
import sys

try:
    import unittest
    from contextlib import contextmanager
    from click.testing import CliRunner
    from tigertrace import cli
    from test_tasks import * 
    from test_stores import *
    from test_features import *
except ImportError as e:
    print('import error:',e)
    raise e


class TestTigertrace(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_command_line_interface(self):
        """
        Check that the command line works
        """
        runner = CliRunner()
        help_result = runner.invoke(cli.main, ['--help'])
        assert help_result.exit_code == 0
        assert 'Show this message and exit.' in help_result.output


class TestTree(unittest.TestCase):

    def test_node_insertion(self):
        from tigertrace.util.tree import BinaryTree
        t = BinaryTree(fromarray=[1])
        t.insert_left_leaf(2)
        t.insert_right_leaf(3)
        self.assertEqual(t.left.key,2)
        self.assertEqual(t.right.key,3)

    def test_tree_in_features(self):
        from tigertrace.features import Tree
        from tigertrace.tasks.task import Agglomeration
        t = Agglomeration()
        t.nodes_features = ['tree']
        f_1 = {'tree': Tree(fromarray=[1])}
        f_2 = {'tree': Tree(fromarray=[1])}
        f_sum = t.sum_nodes_features(f_1, f_2)
        self.assertEqual(f_sum, {'tree': Tree(fromarray=[1])})

class TestConstructTask(unittest.TestCase):
    def test_sum_node_features(self):
        """
        Check if when one supervoxel spans two chunks, it's features are correctly merged
        """
        from tigertrace.features import Tree, Neighbors, SoftLabel
        from tigertrace.tasks.task import Agglomeration
        f_1 = {'neighbors': Neighbors([]), 'tree':Tree(fromarray=[1]),'soft_label': SoftLabel({1: 100}), 'size': 100}
        f_2 = {'neighbors': Neighbors([]), 'tree':Tree(fromarray=[1]),'soft_label': SoftLabel({1: 50, 2:50}), 'size': 100}
        t = Agglomeration()
        t.nodes_features = ['neighbors','tree','soft_label','size']
        features = t.sum_nodes_features(f_1,f_2)
        self.assertEqual(features['neighbors'],Neighbors([]))
        self.assertEqual(features['tree'], Tree(fromarray=[1]))
        self.assertEqual(features['soft_label'], SoftLabel({1:150,2:50}))
        self.assertEqual(features['size'], 200)

class TestEvaluateTask(unittest.TestCase):
    def setUp(self):
        from tigertrace.stores.memory import MemoryStore
        self.store = MemoryStore('/tmp/dataset')

        from tigertrace.queues import LocalQueue
        self.queue = LocalQueue('/tmp/dataset')

    def tearDown(self):
        del self.store
        del self.queue

    def test_boolean_array_simplest_case(self):
        import numpy as np
        from tigertrace.tasks.evaluate import Evaluate

        self.store.put_node(1, {'pos': np.array([[0,0,0]])})
        self.store.put_node(2, {'pos': np.array([[0,0,1]])})
        self.store.put_edge(1,2, {'pos': np.array([[0,0,0.5]])})

        t = Evaluate(1, 2, None)
        t.fetch(self.store, self.queue)

        x_size = 4; y_size=2; z_size=2
        node_1_arr, node_2_arr = t.create_boolean_array(x_size=x_size,y_size=y_size,z_size=z_size)
        node_1_expected_arr = np.zeros(shape=(z_size,y_size,x_size))
        node_1_expected_arr[1,1,1] = 1
        self.assertTrue( np.all(node_1_arr==node_1_expected_arr) )
     
        node_2_expected_arr = np.zeros(shape=(z_size,y_size,x_size))
        node_2_expected_arr[1,1,2] = 1
        self.assertTrue( np.all(node_2_arr==node_2_expected_arr) )

    def test_boolean_array_large_node(self):
        import numpy as np
        from tigertrace.tasks.evaluate import Evaluate

        self.store.put_node(1, {'pos': np.array([[0,0,2],[0,0,3],[0,0,4],[0,0,5],[0,0,6],[0,0,7]])})
        self.store.put_node(2, {'pos': np.array([[0,0,0],[0,0,1]])})
        self.store.put_edge(1,2, {'pos': np.array([[0,0,1.5]])})

        t = Evaluate(1, 2, None)
        t.fetch(self.store, self.queue)

        x_size = 4; y_size=2; z_size=2
        node_1_arr, node_2_arr = t.create_boolean_array(x_size=x_size,y_size=y_size,z_size=z_size)

        node_1_expected_arr = np.zeros(shape=(z_size,y_size,x_size))
        node_1_expected_arr[1,1,2:] = 1
        self.assertTrue( np.all(node_1_arr==node_1_expected_arr) )
     
        node_2_expected_arr = np.zeros(shape=(z_size,y_size,x_size))
        node_2_expected_arr[1,1,0:2] = 1
        self.assertTrue( np.all(node_2_arr==node_2_expected_arr) )

    def test_mean_affinity(self):
        from tigertrace.tasks.evaluate import Evaluate
        self.store.put_node(1, {'size': 10})
        self.store.put_node(2, {'size': 20})
        self.store.put_edge(1,2, {'aff_sum': 4.0 , 'size':8})

        t = Evaluate(1, 2, None)
        t.oracle = False
        t.classify = lambda features: features['mean_affinity']
        t.nodes_features = ['size']
        t.edge_features = ['src','dst','size','aff_sum']
        t.fetch(self.store, self.queue)
        t.run()

        self.assertEqual(self.store.get_edge(1,2)['weight'],0.5)

    def test_mesh(self):
        #there is something wrong with them
        pass

class TestColapseEdgeTask(unittest.TestCase):
    
    def setUp(self):
        from tigertrace.stores.memory import MemoryStore
        self.store = MemoryStore('/tmp/dataset')

        from tigertrace.queues import LocalQueue
        self.queue = LocalQueue('/tmp/dataset')

    def tearDown(self):
        del self.store
        del self.queue

    def test_no_neighbors(self):
        from tigertrace.features import Tree, Neighbors, SoftLabel
        from tigertrace.tasks.task import Agglomeration
        from tigertrace.tasks.collapse import Collapse

        self.store.put_node(1, {'soft_label':SoftLabel({1:1}),'size':1, 'neighbors':Neighbors([2]), 'tree':Tree(fromarray=[1])})
        self.store.put_node(2, {'soft_label':SoftLabel({1:1}),'size':1, 'neighbors':Neighbors([1]), 'tree':Tree(fromarray=[2])})
        self.store.put_edge(1,2, {'aff_sum':1.0 , 'size':1, 'tree':Tree(fromarray=[(1,2)])})

        t = Collapse(1,2, None)
        t.classify = None
        Agglomeration.oracle = True
        Agglomeration.nodes_features = ['tree','neighbors','size','soft_label']
        Agglomeration.edge_features = ['tree','aff_sum','size']
        t.fetch(self.store, self.queue)
        t.run()
        t.save(self.store, self.queue)

        #Old components should have been deleted
        self.assertIsNone(self.store.get_node(1))
        self.assertIsNone(self.store.get_node(2))
        self.assertIsNone(self.store.get_edge(1,2))

        #The new node should exists and be correct
        self.assertEqual(self.store.get_node(3)['neighbors'], Neighbors([]))
        self.assertEqual(self.store.get_node(3)['tree'], Tree(fromarray=[3,1,2]))

    def test_single_neighbor(self):
        self.maxDiff = 1000
        from tigertrace.features import Tree, Neighbors, SoftLabel
        from tigertrace.tasks.task import Agglomeration
        from tigertrace.tasks.collapse import Collapse

        self.store.put_node(1, {'soft_label':SoftLabel({1:1}),'size':1, 'neighbors':Neighbors([2,3]), 'tree':Tree(fromarray=[1])})
        self.store.put_node(2, {'soft_label':SoftLabel({1:1}),'size':1, 'neighbors':Neighbors([1]), 'tree':Tree(fromarray=[2])})
        self.store.put_edge(1,2, {'aff_sum':1.0 , 'size':1, 'tree':Tree(fromarray=[(1,2)])})

        self.store.put_node(3, {'soft_label':SoftLabel({1:1}),'size':1, 'neighbors':Neighbors([1]), 'tree':Tree(fromarray=[3])})
        self.store.put_edge(1,3, {'aff_sum':1.0 , 'size':1, 'tree':Tree(fromarray=[(1,3)])})

        t = Collapse(1,2, None)
        t.classify = None
        Agglomeration.oracle = True
        Agglomeration.nodes_features = ['tree','neighbors','size','soft_label']
        Agglomeration.edge_features = ['tree','aff_sum','size']
        t.fetch(self.store, self.queue)
        t.run()
        t.save(self.store, self.queue)

        #Old components should have been deleted
        self.assertIsNone(self.store.get_edge(1,3))

        new_edge = self.store.get_edge(4,3) #4 is the id of the new node from merging 1 and 2
        self.assertEqual(new_edge,{'aff_sum':1.0 , 'size':1, 'weight':1.0, 'tree':Tree(fromarray=[(3,4),(1,3),-1])})
        self.assertEqual(self.store.get_node(4)['neighbors'],Neighbors([3]))
        self.assertEqual(self.store.get_node(4)['tree'],Tree(fromarray=[4,1,2]))
        self.assertEqual(self.store.get_node(3)['neighbors'],Neighbors([4]))
        self.assertEqual(self.store.get_node(3)['tree'],Tree(fromarray=[3]))

    def test_other_single_neighbor(self):
        from tigertrace.features import Tree, Neighbors, SoftLabel
        from tigertrace.tasks.task import Agglomeration
        from tigertrace.tasks.collapse import Collapse

        self.store.put_node(1, {'soft_label':SoftLabel({1:1}),'size':1, 'neighbors':Neighbors([2]), 'tree':Tree(fromarray=[1])})
        self.store.put_node(2, {'soft_label':SoftLabel({1:1}),'size':1, 'neighbors':Neighbors([1,3]), 'tree':Tree(fromarray=[2])})
        self.store.put_edge(1,2,{'aff_sum':1.0 , 'size':1.0,'tree':Tree(fromarray=[(1,2)])})

        self.store.put_node(3, {'soft_label':SoftLabel({1:1}),'size':1, 'neighbors':Neighbors([2]), 'tree':Tree(fromarray=[3])})
        self.store.put_edge(2,3, {'aff_sum':1.0 , 'size':1.0, 'tree':Tree(fromarray=[(2,3)])})

        t = Collapse(1,2, None)
        t.classify = None
        Agglomeration.oracle = True
        Agglomeration.nodes_features = ['tree','neighbors','size','soft_label']
        Agglomeration.edge_features = ['tree','aff_sum','size']
        t.fetch(self.store, self.queue)
        t.run()
        t.save(self.store, self.queue)

        #Old components should have been deleted
        self.assertIsNone(self.store.get_edge(2,3))
        new_edge = self.store.get_edge(4,3) #4 is the id of the new node from merging 1 and 2
        self.assertEqual(new_edge,{'aff_sum':1.0 , 'size':1, 'weight':1.0,'tree':Tree(fromarray=[(3,4),-1,(2,3)])})
        self.assertEqual(self.store.get_node(4)['neighbors'],Neighbors([3]))
        self.assertEqual(self.store.get_node(4)['tree'],Tree(fromarray=[4,1,2]))
        self.assertEqual(self.store.get_node(3)['neighbors'],Neighbors([4]))
        self.assertEqual(self.store.get_node(3)['tree'],Tree(fromarray=[3]))

    def test_common_neighbor(self):
        from tigertrace.features import Tree, Neighbors, SoftLabel
        from tigertrace.tasks.task import Agglomeration
        from tigertrace.tasks.collapse import Collapse

        self.store.put_node(1, {'soft_label':SoftLabel({1:1}),'size':1, 'neighbors':Neighbors([2,3]), 'tree':Tree(fromarray=[1])})
        self.store.put_node(2, {'soft_label':SoftLabel({1:1}),'size':1, 'neighbors':Neighbors([1,3]), 'tree':Tree(fromarray=[2])})
        self.store.put_edge(1,2, {'aff_sum':1.0 , 'size':1.0,'tree':Tree(fromarray=[(1,2)])})

        self.store.put_node(3, {'soft_label':SoftLabel({1:1}),'size':1, 'neighbors':Neighbors([1,2]), 'tree':Tree(fromarray=[3])})
        self.store.put_edge(1,3, {'aff_sum':1.0 , 'size':1.0,'tree':Tree(fromarray=[(1,3)])})
        self.store.put_edge(2,3, {'aff_sum':1.0 , 'size':1.0,'tree':Tree(fromarray=[(2,3)])})

        t = Collapse(1,2, None)
        t.classify = None
        Agglomeration.oracle = True
        Agglomeration.nodes_features = ['tree','neighbors','size','soft_label']
        Agglomeration.edge_features = ['tree','aff_sum','size']
        t.fetch(self.store, self.queue)
        t.run()
        t.save(self.store, self.queue)

        #Old components should have been deleted
        self.assertIsNone(self.store.get_edge(2,3))
        self.assertIsNone(self.store.get_edge(1,3))
        new_edge = self.store.get_edge(4,3) #4 is the id of the new node from merging 1 and 2
        self.assertEqual(new_edge,{'aff_sum':2.0 , 'size':2.0, 'weight':1.0, 'tree':Tree(fromarray=[(3,4),(1,3),(2,3)])})
        self.assertEqual(self.store.get_node(4)['neighbors'],Neighbors([3]))
        self.assertEqual(self.store.get_node(4)['tree'],Tree(fromarray=[4,1,2]))
        self.assertEqual(self.store.get_node(3)['neighbors'],Neighbors([4]))
        self.assertEqual(self.store.get_node(3)['tree'],Tree(fromarray=[3]))

if __name__ == '__main__':
    sys.exit(unittest.main())
