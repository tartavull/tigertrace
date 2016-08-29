import logging
logger = logging.getLogger(__name__)
import os 
import json

import tornado.ioloop
import tornado.web
from tornado.escape import json_encode
from glob import glob

from tomni.backend.spark import sc, sqlContext
from tomni.backend.datasets import Dataset
from tomni.backend.graph import  Graph
from tomni.backend.util import files
from tomni.backend.nodes import Nodes
from tomni.backend.edges import Edges
from tomni.backend.triplets import Triplets

def return_json(self, obj ):

  self.set_header('Content-type', 'application/json')
  self.set_header('Access-Control-Allow-Origin', '*')
  self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
  self.write(json_encode(obj))

class EdgeInfoHandler(tornado.web.RequestHandler):
  def get(self, dataset, src, dst):
  
    info = hi.get_edge_info(dataset, int(src), int(dst))
    return_json(self, info)
    return

class EdgesHandler(tornado.web.RequestHandler):
  def get(self, dataset ):
  
    edge = hi.get_edge( dataset )
    return_json(self, edge)
    return

  def post(self, dataset):
    decision = json.loads(self.request.body)
    hi.set_human_decision(dataset, decision)

    self.set_header("Content-Type", "text/plain")
    self.set_header('Access-Control-Allow-Origin', '*')
    self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS') 
    self.set_status(200)
    edge = hi.get_edge(dataset)
    return_json(self, edge)
    self.finish()


  def options(self, dataset):
    self.set_header("Content-Type", "text/plain")
    self.set_header('Access-Control-Allow-Headers','Content-Length')
    self.set_header('Access-Control-Allow-Headers','Content-Type')
    self.set_header('Access-Control-Allow-Origin', '*')
    self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS') 
    self.set_status(200)
    self.finish()

class ChunkeHandler(tornado.web.RequestHandler):

  def set_extra_headers(self):
    self.set_header('Content-type', 'application/json')
    self.set_header('Access-Control-Allow-Origin', '*')
    self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
    self.set_header('Content-Encoding', 'gzip')

  def get(self, dataset, filename):
    try:
      p = files.read('/data/{}/chunks/{}'.format(dataset,filename))
      self.clear()
      self.set_extra_headers()
      self.write(p.read())
      self.finish()
      p.close()
    except Exception, e:
      print e
      self.clear()
      self.set_status(404)
      self.finish()



def make_app():

  return tornado.web.Application(handlers=[
    (r'/dataset/(\w+)/edges$', EdgesHandler),
    (r'/dataset/(\w+)/edge_info/(\d*)/(\d*)$', EdgeInfoHandler),
    (r'/dataset/(\w+)/chunk/(.*)$', ChunkeHandler),
  ],
  settings= {
    "compress_response": True,
  })
  #none of this settings seems to work, and responses are sent uncompressed

class HumanInteraction:

  def __init__(self):
    self.load_all_datasets()

  def load_all_datasets(self):
    self.datasets = {}
    for dirname in files.get_all_datasets():

      dataset = Dataset(dirname)
      nodes = Nodes(sc, sqlContext, dataset.chunks, dataset.name)
      edges = Edges(sc, sqlContext, dataset.chunks, dataset.name)
      triplets = Triplets(sc, sqlContext, dataset.name, nodes, edges)

      self.datasets[dirname] = {
        'graph': Graph(dataset.name, nodes, edges, triplets)
      }

      for batch in range(15):
        logger.info('batch = ' + str(batch))
        self.datasets[dirname]['graph'].agglomerate()

  def get_edge(self, dataset):

    d = self.datasets[dataset]
    return d['graph'].get_edges_for_humans()
   
  def get_edge_info(self, dataset ,src, dst):
    d = self.datasets[dataset]
    return d['graph'].get_edge_info( src,dst )    

  def set_human_decision(self, dataset, decision):
    d = self.datasets[dataset]

    logger.info('decision submited' , decision)
    print decision['answer']
    if decision['answer'] == 'y':
      new_weight = 1.0
    else:
      new_weight = 0.0

    d['graph'].set_edge_weight(decision['edge'] , new_weight)

if __name__ == '__main__':
  hi = HumanInteraction()

  app = make_app()
  app.listen(8888)
  tornado.ioloop.IOLoop.current().start()

