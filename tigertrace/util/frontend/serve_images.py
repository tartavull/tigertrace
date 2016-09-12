import h5py
import tornado.ioloop
import tornado.web
import tornado.wsgi
import numpy
import wsgiref.simple_server
import os
from scipy.misc import imsave
import StringIO

cache = {}
cache_segmentation= {}
image = h5py.File('/usr/people/it2/image.h5')
segmentation = h5py.File('/usr/people/it2/machine_labels.h5')
# if 'chunked' not in segmentation:
#   segmentation.create_dataset('chunked',data=segmentation['main'], chunks=(1,128,128),compression="gzip", compression_opts=9)
# print 'dataset created'
def set_headers(self):
  self.set_header('Content-type', 'image/png')
  self.set_header('Access-Control-Allow-Origin', '*')
  self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

class MeshHandler(tornado.web.RequestHandler):
  pass
class ImageHandler(tornado.web.RequestHandler):
    """
    Serve the image binary blobs.
    """
    def get(self, z):
      z = int(z)
      if z not in cache:
        _slice = image['chunked'][int(z),:,:]
        buf = StringIO.StringIO()
        imsave(buf, _slice, format= 'png')
        png = buf.getvalue()
        cache[z] = png

      self.clear()
      set_headers(self)
      self.write(cache[z])

class SegmentationHandler(tornado.web.RequestHandler):
    """
    Serve the image binary blobs.
    """

    def get(self, z):
      z = int(z)
      if z not in cache_segmentation:
        _slice = segmentation['chunked'][int(z),:,:]
        buf = StringIO.StringIO()
        imsave(buf, _slice, format= 'png')
        png = buf.getvalue()
        cache_segmentation[z] = png

      self.clear()
      set_headers(self)
      self.write(cache_segmentation[z])
    

if __name__ == '__main__':

  application = tornado.web.Application([
          (r'/images/(.*)', ImageHandler), 
          (r'/segmentation/(.*)', SegmentationHandler),
          (r'/mesh/(.*)', MeshHandler)],
    compress_response=True)


  wsgi_app = tornado.wsgi.WSGIAdapter(application)
  server = wsgiref.simple_server.make_server('', int(os.environ.get('PORT', 8888)), wsgi_app)
  server.serve_forever()