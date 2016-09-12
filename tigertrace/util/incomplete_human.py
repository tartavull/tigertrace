import pandas
import numpy as np
status =  pandas.read_csv('/usr/people/it2/seungmount/Omni/TracerTasks/Ignacio_free_pizza/human_labels.omni.segments.txt')
status = np.array(status)
import h5py
with h5py.File('/usr/people/it2/seungmount/Omni/TracerTasks/Ignacio_free_pizza/human_labels_incomplete.h5') as f:
  # f.create_dataset('croped', data=f['main'][:157,:2128,:2128])
  f.create_dataset('segment_status',data=status)