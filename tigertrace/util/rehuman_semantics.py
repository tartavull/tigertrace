from tqdm import tqdm
from collections import defaultdict
import h5py
import networkx as nx
import struct
import numpy as np

# hl = None
# ml = None
# with h5py.File('/usr/people/it2/seungmount/research/datasets/blended_piriform_157x2128x2128/all/human_semantic_labels.h5','r') as f:
#   hl = f['main'][:]
# with h5py.File('/usr/people/it2/seungmount/research/datasets/blended_piriform_157x2128x2128/all/sparse_human_labels.h5','r') as f:
#   ml = f['main'][:]


# soft_labels = defaultdict(lambda: defaultdict(int))

# def max_key_from_dict( d ):
#   max_key = d.keys()[0]
#   max_val = d[max_key]
#   for k,v in d.iteritems():
#     if v > max_val:
#       max_val = v
#       max_key = k
#   return max_key

# for z in tqdm(xrange(hl.shape[0])):
#   for y in xrange(hl.shape[1]):
#     for x in xrange(hl.shape[2]):
#       soft_labels[ml[z,y,x]][hl[z,y,x]] += 1


# mapping = dict()
# for ml_label, soft_label in soft_labels.iteritems():
#   best_hl = max_key_from_dict(soft_label)
#   mapping[ml_label] = best_hl


# final = np.zeros(shape=ml.shape)
# for z in tqdm(xrange(hl.shape[0])):
#   for y in xrange(hl.shape[1]):
#     for x in xrange(hl.shape[2]):
#       final[z,y,x] = mapping[ml[z,y,x]]

with h5py.File('/usr/people/it2/seungmount/research/datasets/blended_piriform_157x2128x2128/all/sparse_semantic_labels.h5') as f:
  
  exp = np.zeros(shape=(4,157,2128,2128))
  for i in range(5):
    exp[i,:,:,:] = f['main'][:,:,:] == i
  f.create_dataset('expanded',data=exp)