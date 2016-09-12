import pickle
import numpy as np
import matplotlib.pyplot as plt
import h5py

mean_affinity = []
soft_label = []
soft_label_errors = []
acum_errors = 0
valid_ids = set()
with h5py.File('/usr/people/it2/seungmount/research/datasets/blended_piriform_157x2128x2128/all/sparse_human_labels.h5') as f:
  for seg_id , status in f['segment_status']:
    if status == 2:
      valid_ids.add(seg_id)

  print len(valid_ids)

errors_type = []
with open('/usr/people/it2/seungmount/research/datasets/blended_piriform_157x2128x2128/all/log.p','r') as f:
  for example in np.array(pickle.load(f)):
    # if one supervoxel has been validated, all supervoxels connected to them should have been validated
    # in other words, I just want to ignore, merges that solely include unvalidated stuff
    val_1 = len(set(example['tree_1'].t.get_all_leafs()).intersection(valid_ids)) >= 1
    val_2 = len(set(example['tree_2'].t.get_all_leafs()).intersection(valid_ids)) >= 1
    if val_1 or val_2:
      mean_affinity.append(example['mean_affinity'])
      soft_label.append(example['soft_label'])
      acum_errors += (example['soft_label'] < 0.1)
      soft_label_errors.append( acum_errors )
      if example['soft_label'] < 0.1:
        type_1 = np.argmax(example['semantic_1'])
        type_2 = np.argmax(example['semantic_2'])
        errors_type.append((type_1, type_2))


boundaries = 0
unkown = 1
axons = 2
dendrites = 3
glial = 4
from collections import defaultdict
d = defaultdict(lambda: defaultdict(int))
for e in errors_type:
  e = sorted(e)
  d[e[0]][e[1]] += 1
  if e[0] != e[1]:
    d[e[1]][e[0]] += 1

plt.scatter(mean_affinity,soft_label_errors)
plt.xlabel('mean_affinity')
plt.ylabel('acum_erros')
plt.gca().invert_xaxis()
plt.show()

log = np.array(filtered)

print "total merges :" ,len(log)
print "clearly incorrect:", sum(log[:,soft_label] < 0.1)
print "clearly correct:", sum(log[:,soft_label] > 0.9)


plt.hist(log[:,weight], 50, normed=1, facecolor='green', alpha=0.75, label='weight')
plt.hist(log[:,soft_label], 50, normed=1, facecolor='blue', alpha=0.75, label='soft_label')
plt.xlabel('weight or soft_label')
plt.ylabel('frecuency')
plt.legend()
plt.show()


plt.scatter(log[:,weight],log[:,soft_label])
plt.xlabel('weight')
plt.ylabel('soft_label')
plt.show()

fig = plt.figure()
plt.plot(log[:,weight],linewidth=4)
plt.scatter(range(log.shape[0]), log[:,soft_label].astype(float), c='r', alpha=0.1, s=10, picker=True)
plt.xlabel('time')
plt.ylabel('weight or soft_label')
def onpick(event):
  ind = event.ind
  print log[ind]
  # seg_1 = log[ind][0]
  # seg_2 = log[ind][1]
  # mean_affinity = log[ind][2]
  # soft_label = log[ind][3]
  # print "seg_1: {}\nseg_2:{}\nmean: {} soft: {}\n\n".format(seg_1,
  #                                                       seg_2,
  #                                                       mean_affinity, soft_label)
fig.canvas.mpl_connect('pick_event', onpick)
plt.show()

