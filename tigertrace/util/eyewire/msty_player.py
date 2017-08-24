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
import struct

from retrying import retry
from msty_conf import conf
from mysql import Mysql
conn = Mysql()

GOOGLE_STORAGE_URL = 'https://storage.googleapis.com/{}/{}segmentation.graph'
def _submit_segment_api(segment, task_id):
  segments = ",".join(map(str,segment))
  requests.post('{}/1.0/tasks/{}/submit?access_token={}'
    .format(conf['tasking_url'], task_id, conf['access_token']),json={"segments":segments,"status":"finished","reap":False,"simplified":True,"duration" :0})

def _get_tasks_to_play():
  tasks =  conn.query("""select 
  tasks.id,
  tasks.segmentation_id,
  tasks.seeds, 
  volumes.path,
  datasets.cloud_bucket,
  datasets.mst_threshold
from tasks FORCE KEY (cell_key), cells, cell_tags, volumes, datasets
where
  cell_tags.tag = 'Agglomerator_AI'
  AND cell_tags.value > 0
  AND cells.id = cell_tags.cell_id
  AND datasets.mst_threshold IS NOT NULL
  AND cells.completed is null
  AND tasks.cell = cells.id
  AND tasks.status = 0
  AND tasks.segmentation_id = volumes.id
  AND volumes.dataset = datasets.id
  AND (
    select count(1) 
    from validations 
    where validations.task_id = tasks.id and validations.status = 0
  ) = 0
  limit 1000;""")

  return tasks

def _agglomerate(g, seeds, threshold=0.35):
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

def _create_nx_graph_json(mst):
  g = nx.Graph()
  for u,v, weight in mst:
    g.add_edge(u,v,weight=weight)
  return g

def _create_nx_graph_raw(mst_raw):
  g = nx.Graph()
  for offset in range(0, len(mst_raw), 8):
    u, v, weight = struct.unpack('HHf', mst_raw[offset:offset+8])
    g.add_edge(u,v,weight=weight)
  return g

@retry(wait_exponential_multiplier=1000, wait_exponential_max=30000)
def start_loop():
  print "(Re)starting Msty..."
  while True:
    time_slept = 0.0
    for task_id, segmentation_id, seeds, path, cloud_bucket, mst_threshold in _get_tasks_to_play():
      print "Playing task " + str(task_id)
      seeds = map(int,json.loads(seeds).keys())
      if cloud_bucket:
        while True: # Weird random connection errors
          try:
            mst_raw = requests.get(GOOGLE_STORAGE_URL.format(cloud_bucket, path), timeout=5).content
          except requests.exceptions.ConnectionError:
            print "Timeout while fetching mst for task " + str(task_id)
            time.sleep(1)
            time_slept += 6
            continue
          break
          
        mst = _create_nx_graph_raw(mst_raw)
      else:
        r = requests.get('http://mst.eyewire.org/segmentation/{}'.format(segmentation_id))
        mst = _create_nx_graph_json(r.json())

      segment = _agglomerate(mst, seeds, mst_threshold)
      _submit_segment_api(segment, task_id)
      time.sleep(0.05)
      time_slept += 0.05
    if time_slept < 5.0:
      print "Sleep for " + str(5.0 - time_slept) + " seconds..."
      time.sleep(5.0 - time_slept)

if __name__ == '__main__':
  start_loop()

