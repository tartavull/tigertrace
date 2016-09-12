import logging
from multiprocessing import Pool
import cloudpickle
from time import sleep

from tigertrace.tasks import tasks_dict, Agglomeration
from tigertrace.tasks.construct import Construct
from tigertrace.tasks.evaluate import Evaluate

#Pickling magic for class methods from
#https://bytes.com/topic/python/answers/552476-why-cant-you-pickle-instancemethods
def _pickle_method(method):
    func_name = method.im_func.__name__
    obj = method.im_self
    cls = method.im_class
    return _unpickle_method, (func_name, obj, cls)

def _unpickle_method(func_name, obj, cls):
    for cls in cls.mro():
        try:
            func = cls.__dict__[func_name]
        except KeyError:
            pass
        else:
            break
    return func.__get__(obj, cls)

import copy_reg
import types
copy_reg.pickle(types.MethodType, _pickle_method, _unpickle_method)
###################################################################################

class Worker(object):
    """
    There should be one of this per node
    Each worker can run many tasks in parallel
    if enough resources are available.
    
    Instead of individually locking the methods of the store and the 
    Queue. We pass a lock to each tasks, making the task responsible
    for locking the required parts.

    A task can also choose to not run in another process by setting
    async to false.

    It seems that running in another process is not worth for constructing the graph.
    The task has to be serialize, and later deserialize in the parent process, so that
    the changes to the queue and store are applied to the queue and the store of the 
    parent process.
    """
    def __init__(self, store, queue, classifier, just_build=False, oracle=False):
        

        self.just_build = just_build
        self.oracle = oracle
        self.classifier = classifier
        self.store = store
        self.queue = queue
        self.sampler = 1#Sampler()
        self.processes = 8
        self.running_tasks = 0
        self.last_task = None
        self.process_task()
        # self.pool.close()
        # self.pool.join()

    def process_task(self):
        # self.pool = Pool(self.processes)
        while len(self.queue) or self.running_tasks:
            try:
                task_name, task_args = self.queue.get_next_task()
            except StopIteration:
                sleep(1)
                continue

            print('processing {}:{}'.format(task_name, task_args))
            if task_name == Evaluate.__name__ and self.just_build:
                #put this task back in the queue
                self.queue.submit_new_task(task_name, task_args)
                self.queue.dump()
                self.store.dump()
                return  

            args = task_args+ (self.sampler,)
            task = tasks_dict[task_name](*args)
            task.oracle = self.oracle
            task.classifier = self.classifier
            task.fetch(self.store, self.queue)
            if task.async:
                if self.running_tasks >= self.processes:
                    self.last_task.wait()
                self.running_tasks += 1
                self.last_task = self.pool.apply_async(task.run, callback=self.callback)
            else:
                task.run()
                task.save(self.store, self.queue)
    
    def callback(self, value):
        save = cloudpickle.loads(value)
        save(self.store, self.queue)
        self.running_tasks -= 1