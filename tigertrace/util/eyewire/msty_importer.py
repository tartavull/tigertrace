import os
import cPickle as pickle

from construct import *
from tqdm import tqdm

from mysql import Mysql
conn = Mysql()



def _parse_binary(path, segmentation_id, output_dir):
    with open('{}/users/_default/segmentations/segmentation1/segments/mst.data'.format(path),'r') as f:
      bin_mst = f.read()

    c = GreedyRange(
        Struct("row",
         ULInt32("index"),
         ULInt32("id_1"),
         ULInt32("id_2"),
         Padding(4),
         LFloat64("max_affinity"),
         Padding(8)
        )
      )

    mst = []
    for edge in  c.parse(bin_mst):
      mst.append([int(edge.id_1), int(edge.id_2), float(edge.max_affinity)])
    pickle.dump( mst, open( "{}/{}.p".format(output_dir,segmentation_id), "wb" ) )

def import_msts_from_omni(dataset=3, output_dir="/usr/people/it2/msts"):
  for segmentation_id, omni_path in tqdm(conn.query("select  id, path  from volumes where datatype=2 and dataset={};".format(dataset))):    
    if os.path.isfile("/usr/people/it2/msts/{}.p".format(segmentation_id)):
      continue

    try:
      _parse_binary(omni_path,segmentation_id, output_dir)
    except Exception, e:
      print e
      print 'failed to get',segmentation_id
if __name__ == '__main__':
  import_msts_from_omni(10)