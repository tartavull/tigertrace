from tqdm import tqdm
from collections import defaultdict
import h5py
import networkx as nx
import struct

hl = None
ml = None
with h5py.File('/usr/people/it2/seungmount/research/datasets/blended_piriform_157x2128x2128/all/human_labels.h5','r') as f:
  hl = f['main'][:]
with h5py.File('/usr/people/it2/seungmount/research/datasets/blended_piriform_157x2128x2128/all/machine_labels.h5','r') as f:
  ml = f['main'][:]


soft_labels = defaultdict(lambda: defaultdict(int))

def max_key_from_dict( d ):
  max_key = d.keys()[0]
  max_val = d[max_key]
  for k,v in d.iteritems():
    if v > max_val:
      max_val = v
      max_key = k
  return max_key

for z in tqdm(xrange(hl.shape[0])):
  for y in xrange(hl.shape[1]):
    for x in xrange(hl.shape[2]):
      if hl[z,y,x] == 0 or ml[z,y,x] == 0:
        continue
      soft_labels[ml[z,y,x]][hl[z,y,x]] += 1


components = defaultdict(set)
for ml_label, soft_label in soft_labels.iteritems():
  if len(soft_label) == 0:
    continue
  best_hl = max_key_from_dict(soft_label)
  if best_hl == 74554:
    print ml_label, soft_label, best_hl
  components[best_hl].add(ml_label)


mst = bytearray()
i = 0
for best_hl, ml_set in components.iteritems():
  ml_list = list(ml_set)
  root_node = ml_list[0]
  for node in ml_list[1:]:
    print node, root_node
    i += 1
    mst.extend(struct.pack('<IIIIdd',i,node, root_node,0, 1.0,0.0))

with open('mst.data','wb') as f:
  f.write(mst)
