import pickle
import numpy as np
import matplotlib.pyplot as plt
with open('/usr/people/it2/tigress/agg/blended_piriform_157x2128x2128/train/log.p','r') as f:
  log = np.array(pickle.load(f))

# plt.hist(log[:,0], 50, normed=1, facecolor='green', alpha=0.75, label='weight')
# plt.hist(log[:,1], 50, normed=1, facecolor='blue', alpha=0.75, label='soft_label')
# plt.legend()
# plt.show()


# plt.scatter(log[:,0],log[:,1])
# plt.show()

plt.plot(log[:,0],linewidth=4)
plt.plot(log[:,1], 'ro', alpha=0.1)
plt.show()