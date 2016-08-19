#Create a file in this folder
#called mysql_conf.py
#that includes
# conf = {  
#   'access_token': ''
# }

import json
import time

import requests
import networkx as nx

from msty_conf import conf
from mysql import Mysql
conn = Mysql()

def _submit_segment_api(segment, task_id):
  segments = ",".join(map(str,segment))
  requests.post('https://beta-tasking.eyewire.org/1.0/tasks/{}/submit?access_token={}'
    .format(task_id, conf['access_token']),json={"segments":segments,"status":"finished","reap":False,"simplified":True,"duration" :0})

def _get_tasks_to_play():
  tasks =  conn.query("""select 
  tasks.id,
  tasks.segmentation_id,
  tasks.seeds, 
  volumes.path
from tasks, cells, cell_tags , volumes
where
  cell_tags.tag = 'Agglomerator_AI'
  AND cell_tags.value > 0
  AND cells.id = cell_tags.cell_id
  AND cells.dataset_id = 10
  AND cells.completed is null
  AND tasks.cell = cells.id
  and tasks.status = 0
  and tasks.segmentation_id = volumes.id
  AND (
    select count(1) 
    from validations 
    where validations.task_id = tasks.id and validations.status = 0
  ) = 0
  limit 1000;""")

  return tasks

def _agglomerate(mst, seeds, threshold=0.35):
  g = _create_nx_graph(mst)
  segment = set(seeds)
  visited = set(seeds)
  to_visit = seeds

  while len(to_visit):
    node = to_visit.pop()
    visited.add(node)
    if node not in g:
      continue
      
    for neighbor in g.neighbors_iter(node):
      if neighbor in visited:
        continue
      if g.edge[node][neighbor]['weight'] > threshold:
        segment.add(neighbor)
        to_visit.append(neighbor)
  return segment

def _create_nx_graph(mst):
  g = nx.Graph()
  for u,v, weight in mst:
    g.add_edge(u,v,weight=weight)
  return g


if __name__ == '__main__':

  while (True):
    for task_id, segmentation_id, seeds , path in _get_tasks_to_play():
      seeds = map(int,json.loads(seeds).keys())
      r = requests.get('http://mst.eyewire.org/segmentation/{}'.format(segmentation_id))
      segment = _agglomerate(r.json(), seeds)
      _submit_segment_api(segment, task_id)
      time.sleep(1)
  time.sleep(10)