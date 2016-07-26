
from tigertrace.queues import LocalQueue
from tigertrace.workers import Worker
from tigertrace.stores.memory import MemoryStore

path = '/usr/people/it2/small_piriform'
task = 'infer'

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
