from __future__ import print_function
import time
from collections import defaultdict
from heapq import heappop, heappush

from six.moves import cPickle as pickle

class Queue(object):
  def submit_new_task( task_name, task_args ):
    pass


class LocalQueue(Queue):
  def __init__(self, dataset_path):
    self.dataset_path = dataset_path
    self.q =[]
    self.frequency = dict()
    self.entry_finder = set()

  def submit_new_task(self, task_name , task_args=tuple(), priority=2.0):
    task = (task_name, task_args) 
    entry = [-priority, task]
    self.entry_finder.add(task)
    heappush(self.q, entry)
  
  def remove_task(self, task_name, task_args):
    'Mark an existing task as REMOVED.  Raise KeyError if not found.'
    task = task_name, task_args
    try:
      self.entry_finder.remove(task)
    except KeyError:
      pass

  def get_next_task(self):
    'Remove and return the highest priority task. Raise KeyError if empty.'
  
    while self.q:
      priority, task = heappop(self.q)
      if task in self.entry_finder:
        task_name, task_args = task
        self.frequency[task_name] = self.frequency.get(task_name,0) + 1
        self.entry_finder.remove(task)
        return task[0] , task[1]
    raise StopIteration

  def __str__(self):
    return str(self.q) + str(self.frequency)

  def __len__(self):
    return len(self.q)

  def __del__(self):
    print(self.frequency)

  def dump(self):
    with open(self.dataset_path + '/queue','wb') as f:
      pickle.dump((self.q,self.frequency,self.entry_finder), f)

  def restore(self):
    with open(self.dataset_path + '/queue','rb') as f:
      self.q, self.frequency, self.entry_finder = pickle.load(f) 