# -*- coding: utf-8 -*-
import logging
import click
import sys
sys.setrecursionlimit(10000)

from .queues import LocalQueue
from .workers import Worker
from .stores.memory import MemoryStore

@click.command()
@click.option('--path', prompt='Path to dataset',
              help='Path to the dataset you want to process.', type=click.Path(exists=True))
@click.option('--task', prompt='Task you want to execute',
              help='What do you want me to do with the dataset?', type=click.Choice(['build', 'restore','train','infer']))


#tasks should be a mutiple options, such that we can execute many tasks together
# Similarly to nargs, there is also the case of wanting to support a 
#parameter being provided multiple times to and have all values recorded 
#– not just the last one. For instance, git commit -m foo -m bar 
#would record two lines for the commit message: foo and bar. 
#This can be accomplished with the multiple flag:

# Example:

# @click.command()
# @click.option('--message', '-m', multiple=True)
# def commit(message):
#     click.echo('\n'.join(message))



def main(path,task):
    """Console script for tigertrace"""
    logging.debug(path)
    logging.debug(task)

    #TODO think of better task division
    if task == 'build':
        queue = LocalQueue(path)
        queue.submit_new_task('Ingest')
        store = MemoryStore(path)
        Worker(store, queue, just_build=True, oracle=True)
    elif task == 'restore':
        queue = LocalQueue(path)
        queue.restore()
        store = MemoryStore(path)
        store.restore()
        queue.submit_new_task('Export',priority=-1.0)
        Worker(store, queue, oracle=True)
    elif task == 'train':
        queue = LocalQueue(path)
        store = MemoryStore(path)
        queue.submit_new_task('Train')
        Worker(store, queue, oracle=True)
    elif task == 'infer':
        queue = LocalQueue(path)
        queue.restore()
        store = MemoryStore(path)
        store.restore()
        queue.submit_new_task('Export',priority=-1.0)
        Worker(store, queue, oracle=False)
 
if __name__ == "__main__":
    main()
