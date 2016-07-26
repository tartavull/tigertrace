import numpy as np
import itertools

from tigertrace.tasks.task import Task

class Ingest(Task):
	"""
	It divides the dataset into chunks (of size chunk_size), and create tasks to independently
	import them.
	"""

	def __init__(self, sampler=None):
		"""
		The sampler is an input such that all task have the same API, but is not actually used.
		"""
		self.chunk_size = np.array([157,1064,1064])  #z,y,x
		self.overlap = 1
			
	def fetch(self, store, queue):
		"""
		It only needs to know the size of the whole dataset to know how to divide it.
		It assumes that we want to import the whole dataset, and that the origin is (0,0,0)
		Also, because the dataset is read from hdf5 which are z,y,x ordered, that convention is kept
		in this class and in others.
		"""
		self.shape = store.get_dataset_shape()
		
	def run(self):
		"""
		It computes a 3 dimensional array, that specify the number of chunks in each dimension.
		"""
		n_chunks = np.ceil( self.shape / self.chunk_size.astype(float) ).astype(int)
		self.n_chunks = np.maximum( n_chunks, np.array([1,1,1]))

	def save(self, store, queue):
		"""
		It iterates over every chunk, creating a task for it.
		Every tasks contains the coordinates in voxels of the min,min,min and max,max,max
		of the bounding box. It also contains a boolean 3d dimensional vector `chunk_overlap`
		which specifies if the faces of the chunks matches with the max faces of the dataset.

		When we compute features that depends on adjacent voxels, we need chunks with a 1 voxel overlap
		so that we count every pair of adjacent voxels. But some voxels(the one in the boundaries) doesn't
		have any adjacent voxel on the boundary direction, we specify that this chunk has a boundary by 
		using that chunk_overlap vector. I know this is a bit confusing, why don't you read the Construct
		class ?
		"""
		for chunk_position in itertools.product(*list(map(range,self.n_chunks))):
			start = np.maximum(np.array(chunk_position) * self.chunk_size, np.array([0,0,0]))
			end =  np.minimum((np.array(chunk_position) + 1) * self.chunk_size + self.overlap, self.shape)
			chunk_overlap = (end != self.shape) * self.overlap	
			queue.submit_new_task('Construct', 
				(tuple(start), tuple(end) , tuple(chunk_overlap)))