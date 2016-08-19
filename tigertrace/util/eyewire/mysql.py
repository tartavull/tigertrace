#Create a file in this folder
#called mysql_conf.py
#that includes
# conf = {  
#   'host': '',
#   'user': '',
#   'passwd': '',
#   'database': '',
#   'port': 3306
# }
from mysql_conf import conf
import pymysql
import numpy as np

class Mysql:
 
  connection = None
  def __del__(self):
    if self.connection is not None:
      self.connection.close()
      self.connection = None

  def maybe_connect(self):
    if self.connection is None:
      self.connection = pymysql.connect(**conf)
      self.connection.autocommit(True)

  def query(self, stringQuery):
    self.maybe_connect()
    cursor = self.connection.cursor(pymysql.cursors.Cursor)
    cursor.execute(stringQuery)
    return cursor.fetchall()

if __name__ == '__main__':
  
  conn = Mysql()
  print conn.query("select  id, path  from volumes where dataset=9 and datatype=2 limit 5;")