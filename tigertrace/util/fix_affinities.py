import h5py

f_in = h5py.File('/usr/people/it2/seungmount/research/datasets/blended_piriform_157x2128x2128/machine_labels.h5')
f_train = h5py.File('/usr/people/it2/seungmount/research/datasets/blended_piriform_157x2128x2128/train_machine_labels.h5')
f_train.create_dataset('main', data=f_in['main'][:,:1064,:])
f_train.close()


f_test = h5py.File('/usr/people/it2/seungmount/research/datasets/blended_piriform_157x2128x2128/test_machine_labels.h5')
f_test.create_dataset('main', data=f_in['main'][:,1064:,:])
f_test.close()
f_in.close()