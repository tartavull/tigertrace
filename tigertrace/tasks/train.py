from six.moves import cPickle as pickle
import itertools
from glob import glob
import numpy as np
import matplotlib.pyplot as plt
import logging
from tigertrace.tasks.task import Task, Agglomeration
from sklearn import tree
from sklearn.ensemble import RandomForestClassifier
from tqdm import tqdm

def classifier(dataset_path):
	t = Train()
	with open(dataset_path + '/model.p', 'rb') as f:
		clf = pickle.load(f)

	def predict(features):
		pred = clf.predict(np.asarray([t._parse_features(features)],dtype=np.float32))[0]
		if pred:
			return features['mean_affinity']
		else:
			return 0.2


		# return clf.predict(np.asarray([t._parse_features(features)],dtype=np.float32))[0][1]
		
	return predict

class Train(Task):
	def __init__(self, sampler=None):
		if 'semantic_sum' in Agglomeration.nodes_features:
			self.feature_names = ['mean_affinity','size_1','size_2','edge_size','semantic_sum']
		else:	
			self.feature_names = ['mean_affinity','size_1','size_2','edge_size']
		
		self.x = []
		self.y = []
		self.all_examples = []

	def fetch(self, store, queue):
		for file in tqdm(glob(store.dataset_path + '/triplets/*.p')):
			logging.debug(file)
			with open(file,'r') as f:
				for example in pickle.load(f):
					if 0.2 < example['soft_label'] and example['soft_label'] < 0.8:
						continue
					self.x.append(self._parse_features(example))
					self.y.append(int(round(example['soft_label'])))
					self.all_examples.append(example)
		self.model_path = store.dataset_path + '/model.p'

	def _parse_features(self, features):
		return [features[key] for key in self.feature_names]

	def train_tree(self):
		self.x = np.array(self.x)
		self.y = np.array(self.y)
		self.clf = tree.DecisionTreeClassifier(max_depth=4, min_samples_split=len(self.x) / 8,criterion='entropy', class_weight=None)
		# self.clf = RandomForestClassifier(min_samples_split=len(self.x) / 8, class_weight='balanced')
		# with open(self.model_path, 'rb') as f:
		# 	self.clf = pickle.load(f)

		self.clf.fit(self.x, self.y)
		self.pred = self.clf.predict(self.x)

	def display_accuracy(self):
		from sklearn.metrics import classification_report
		print(classification_report(self.y, self.pred))
		import itertools
		self.colors = []
		self.classes = []
		self.x_pruned = []
		for i in range(len(self.y)):
			if self.y[i]:
				if self.pred[i]:
					pass
					self.colors.append('green')
					self.classes.append("tp")
				else:
					self.colors.append('darkolivegreen')
					self.classes.append("fn")
					self.x_pruned.append(self.x[i])
			else:
				if not self.pred[i]: #tn
					pass
					self.colors.append('red')
					self.classes.append("tn")      
				else:
					self.x_pruned.append(self.x[i])
					self.colors.append('tomato')        
					self.classes.append("fp")
		self.x_pruned = np.array(self.x_pruned)

	def save_tree_png(self, store):
		import pydot
		from sklearn.externals.six import StringIO 
		dot_data = StringIO()  
		tree.export_graphviz(self.clf, out_file=dot_data,  
							   feature_names=self.feature_names)
		graph = pydot.graph_from_dot_data(dot_data.getvalue())[0]
		with open(store.dataset_path + '/tree.png','wb') as f:
			f.write(graph.create_png())

	def save_scatters_png(self, store):
		combinations = list(itertools.combinations(self.feature_names,2))
		fig = plt.figure(figsize=(20,70),dpi=400)
		for i, comb in enumerate(combinations):
			logging.debug(comb)
			plt.subplot(len(combinations),1,i+1)
			plt.scatter(self.x_pruned[:,self.feature_names.index(comb[0])],
						self.x_pruned[:,self.feature_names.index(comb[1])],
						c=self.colors,label=self.classes, s=5, edgecolor='')
			plt.xlabel(comb[0])
			plt.ylabel(comb[1])
		plt.savefig(store.dataset_path +'/scatters.png')

	def plot_interactive_scatter(self, feature_1, feature_2):
		fig = plt.figure()
		plt.scatter(self.x[:,self.feature_names.index(feature_1)],
			self.x[:,self.feature_names.index(feature_2)],
			c=self.colors,label=self.classes, picker=True)
		plt.xlabel(feature_1)
		plt.ylabel(feature_2)
		def onpick(event):
			ind = event.ind
			logging.info('onpick scatter:', self.all_examples[ind])
		fig.canvas.mpl_connect('pick_event', onpick)
		plt.show()

	def run(self):
		self.train_tree()
		self.display_accuracy()
		# self.plot_interactive_scatter('mean_affinity','semantic_sum')
 
	def save(self, store, queue):
		self.save_scatters_png(store)
		self.save_tree_png(store)
		# with open(store.dataset_path + '/model.p', 'wb') as f:
		# 	pickle.dump(self.clf, f)
		
