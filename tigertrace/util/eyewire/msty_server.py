import tornado
import tornado.ioloop
import tornado.web
from tornado.escape import json_encode

import json
import pickle


import os.path
def return_json(self, obj ):

  self.set_header('Content-type', 'application/json')
  self.set_header('Access-Control-Allow-Origin', '*')
  self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
  self.write(json_encode(obj))

class mstHandler(tornado.web.RequestHandler):
  def get(self, seg_id):
    
    path = '/home/ubuntu/msts/{}.p'.format(seg_id)
    if not os.path.isfile(path):
      self.clear()
      self.set_status(400)
      self.finish("Sorry bro, couldnt find an mst for you")
    
    with open(path) as p:
      return_json(self, pickle.load(p))

def make_app():
  return tornado.web.Application(handlers=[
    (r'/segmentation/(\d+)$', mstHandler)])

if __name__ == '__main__':
  app = make_app()
  app.listen(9000)
  tornado.ioloop.IOLoop.current().start()
