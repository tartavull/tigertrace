import unittest

class TestSoftLabel(unittest.TestCase):
    
    def test_dot_product_no_overlapping(self):
        from tigertrace.features import SoftLabel
        node_1 = SoftLabel({1:10, 2:10})
        node_2 = SoftLabel({3:10, 4:10})
        self.assertEqual(SoftLabel.triplet_feature(node_1,node_2),0)

    def test_dot_product_full_overlap(self):
        from tigertrace.features import SoftLabel
        node_1 = SoftLabel({1:10, 2:10})
        node_2 = SoftLabel({1:10, 2:10})
        self.assertEqual(SoftLabel.triplet_feature(node_1,node_2), 10*10 + 10*10)

    def test_dot_product_partial_overlap(self):
        from tigertrace.features import SoftLabel
        node_1 = SoftLabel({1:10, 2:10})
        node_2 = SoftLabel({2:10, 3:10})
        self.assertEqual(SoftLabel.triplet_feature(node_1,node_2), 10*10)

