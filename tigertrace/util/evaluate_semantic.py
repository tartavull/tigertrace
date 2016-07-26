import h5py
from tqdm import tqdm
import numpy as np
np.set_printoptions(suppress=True)

with h5py.File('/usr/people/it2/seungmount/research/datasets/blended_piriform_157x2128x2128/train/machine_semantic_labels.h5','r') as f:
  pred =  f['main'][:]

with h5py.File('/usr/people/it2/seungmount/research/datasets/piriform_157x2128x2128/train/human_semantic_labels.h5','r') as f:
  truth =  f['main'][:]

# import random
# import numpy
# from matplotlib import pyplot

# bins = numpy.linspace(0.0, 1.0, 100)

# pyplot.hist(main[2,:,:,:].flatten(), bins, alpha=0.5, label='axons')
# pyplot.hist(main[3,:,:,:].flatten(), bins, alpha=0.5, label='dendrites')
# pyplot.hist(main[3,:,:,:].flatten(), bins, alpha=0.5, label='glial')
# pyplot.legend(loc='upper right')
# pyplot.show()

from collections import defaultdict
errors = defaultdict(lambda : defaultdict(int))

arr = np.zeros_like(truth)
for z in tqdm(xrange(pred.shape[1])):
  for y in xrange(pred.shape[2]):
    for x in xrange(pred.shape[3]):
      arr[z,y,x] = np.argmax(pred[:,z,y,x])
      errors[truth[z,y,x]][np.argmax(pred[:,z,y,x])] += 1

# with h5py.File('/usr/people/it2/test_thresholded_machine_semantic_labels.h5') as f:
#   f.create_dataset('main',data=arr)

print errors