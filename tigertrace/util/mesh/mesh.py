import operator
import numpy as np

from skimage import measure
from collections import defaultdict
import itertools


from StringIO import StringIO
import tempfile

#To fix normnals
from trimesh import Trimesh

from mayavi import mlab
from tvtk.api import tvtk

    
def marche_cubes( ids , volume):
  """ 
  Given a segmentation volume and set of ids, 
  it first computes a boolean volume, where every voxel 
  which correspond to an id present in the ids set is set to true.
  It then create a mesh in the boundaries between true and false.
  
  The generated mesh guarantees coherent orientation as of 
  version 0.12. of scikit-image
  
  Args:
      ids (tuple): segment ids that we want to generate a mesh from.
      volume (numpy.array): volume to process
  """

  shape = volume.shape
  volume = np.in1d(volume,ids).reshape(shape)

  try:
    vertices, triangles =  measure.marching_cubes(volume, 0.4)

  except Exception, e:
    return np.array([]), np.array([])

  #We rather work for integers that with floats, there are only .5 values
  vertices = vertices * 2
  vertices = vertices.astype(np.uint16)

  return vertices , triangles

def normalize_v3(arr):
    """ Normalize a numpy array of 3 component vectors shape=(n,3) """
    lens = np.sqrt( arr[:,0]**2 + arr[:,1]**2 + arr[:,2]**2 )

    #hack
    lens[ lens== 0.0 ] = 1.0
    
    arr[:,0] /= lens
    arr[:,1] /= lens
    arr[:,2] /= lens                
    return arr

def compute_normals(vertices, triangles):
  #Create a zeroed array with the same type and shape as our vertices i.e., per vertex normal
  norm = np.zeros( vertices.shape, dtype=vertices.dtype )
  #Create an indexed view into the vertex array using the array of three indices for triangles
  tris = vertices[triangles]
  #Calculate the normal for all the triangles, by taking the cross product of the vectors v1-v0, and v2-v0 in each triangle             
  n = np.cross( tris[::,1 ] - tris[::,0]  , tris[::,2 ] - tris[::,0] )
  # n is now an array of normals per triangle. The length of each normal is dependent the vertices, 
  # we need to normalize these, so that our next step weights each normal equally.
  normalize_v3(n)
  # now we have a normalized array of normals, one per triangle, i.e., per triangle normals.
  # But instead of one per triangle (i.e., flat shading), we add to each vertex in that triangle, 
  # the triangles' normal. Multiple triangles would then contribute to every vertex, so we need to normalize again afterwards.
  # The cool part, we can actually add the normals through an indexed view of our (zeroed) per vertex normal array
  norm[ triangles[:,0] ] += n
  norm[ triangles[:,1] ] += n
  norm[ triangles[:,2] ] += n
  normalize_v3(norm)

  return norm

def render_opengl(vertices, normals,  triangles):
  import pygame
  from pygame import locals as pyl

  from OpenGL import GL as gl
  from OpenGL import GLU
  pygame.init()
  display = (800,600)
  pygame.display.set_mode(display,  pyl.DOUBLEBUF| pyl.OPENGL)

  # To render without the index list, we create a flattened array where
  # the triangle indices are replaced with the actual vertices.

  # first we create a single column index array
  tri_index = triangles.reshape( (-1) )        
  # then we create an indexed view into our vertices and normals
  va = vertices[ tri_index ]
  va /= 128
  no = normals[ tri_index ]        


  while True:
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        pygame.quit()
        gl.quit()

    gl.glEnableClientState( gl.GL_VERTEX_ARRAY )
    gl.glEnableClientState( gl.GL_NORMAL_ARRAY )
    gl.glVertexPointer( 3, gl.GL_FLOAT, 0, va )
    gl.glNormalPointer( gl.GL_FLOAT,    0, no )
    gl.glDrawArrays(gl.GL_TRIANGLES,    0, len(va) )
    gl.glRotatef(1, 3, 1, 1)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT|gl.GL_DEPTH_BUFFER_BIT)
    pygame.display.flip()
    pygame.time.wait(10)


def get_adjacent( vertices, triangles ):
  """ Converts the clasical repretesentation of a mesh
      to a hash table of adjacency of vertices.
      Clasical repretesentation meaning a list of triples
      repretesenting the position of each vertex, and a list
      of triangles where each value referes to the position in
      the list of a vertice.
      The adjacency repretesentation return here, is a hash table
      where the key is a vertex triplets, and its maps into a set
      of vertices triplets.
      It takes O(1) to check if a vertex exist, as well as getting
      the adjacet vertices to it. This two operations are really
      important for the project.
      If using the clasical repretesentation It would take O(n) to
      check for vertex existence, and also O(n) to retrieve all the
      adjacents vertices.
  """

  adj = defaultdict(set)
  for t in triangles:

    v_0 = tuple( vertices[t[0]] )
    v_1 = tuple( vertices[t[1]] )
    v_2 = tuple( vertices[t[2]] )

    adj[v_0].add( v_1 ); adj[v_0].add( v_2 )
    adj[v_1].add( v_0 ); adj[v_1].add( v_2 )
    adj[v_2].add( v_0 ); adj[v_2].add( v_1 )

  return adj

def get_vertices_triangles( adj ):
  """
    Converts from the adjacency representation to the
    vertices triangles one.
  """

  vertices = dict() 
  vertex_counter = 0
  for vertex in adj:
    vertices[vertex] = vertex_counter
    vertex_counter += 1

  triangles = set()
  for vertex_1 in adj:
    adj_vertices = list(adj[vertex_1])

    d = lambda vertex_2: np.linalg.norm(np.array(vertex_1) - np.array(vertex_2))
    filterd_vertices = []
    for adj_vertex in adj_vertices:
      if d(adj_vertex) <= 2.1:
        filterd_vertices.append(adj_vertex)

    if len(filterd_vertices) < 2:
      continue

    for pair in itertools.combinations(filterd_vertices, 2):
      triangle = vertices[vertex_1] , vertices[pair[0]], vertices[pair[1]]
      triangles.add(triangle)


  vertices = map(lambda x: x[0] , sorted(vertices.items(), key=operator.itemgetter(1)))
  return np.array(vertices), np.array(list(triangles))

def find_matching_vertices( adj_1, adj_2 ):
  """ Given two meshes represented as adjcents (see get_adjacent)
      It returns the vertices which belongs to both meshes.

      It takes O(n) time being n, the number of vertices of the 
      smaller mesh.
      This is unnecesary, we could get the matching points by 
      doing a single pass through the volume
  """

  #Itereate over the mesh with less vertices
  if len(adj_1) > len(adj_2):
    adj_1, adj_2 = adj_2, adj_1

  matches = []
  for vertex in adj_1:
    if vertex in adj_2:
      matches.append(vertex)

  return matches

def get_patch( id_1 , id_2,  matches_adj_adj, volume, translation=np.array([0,0,0]) ):
  """Given two meshes represented as adjcents (see :func:get_adjacent)
  It returns another mesh which wraps the contact region of 
  both meshes, also represented as adjacents.
  
  Args:
      id_1 (int): Segment id
      id_2 (int): Segment id
      matches_adj_adj (list): list of triplets with voxel x y z postion
      volume (numpy.array): segmentation array
  """

  patch_adj = defaultdict(set)
  for vertex in matches_adj_adj:
    s_origin, s_slice = get_surrounding_vertex( vertex )
    vertices, triangles = marche_cubes( (id_1, id_2) , volume[s_slice] )
    if not len(vertices):
      continue
    vertices = vertices + s_origin + np.array(translation) * 2
    vertex_adj = get_adjacent( vertices, triangles )
    patch_adj = merge_adjacents( patch_adj, vertex_adj )

  return patch_adj

def merge_meshes(v_1, t_1, v_2, t_2):
  """ Given two meshes represented as lists of vertices,
      and triangles, it merges them returning a new mesh
      using the same repretesentation

      It doesn't do anything smart about removing duplicate
      vertices or triangles."""

  offset = len(v_1)
  v_1 = list(v_1)
  t_1 = list(t_1)
  v_2 = list(v_2)

  for triangle in t_2:
    vertex_idx_0 = triangle[0] + offset
    vertex_idx_1 = triangle[1] + offset
    vertex_idx_2 = triangle[2] + offset
    t_1.append( np.array([vertex_idx_0, vertex_idx_1, vertex_idx_2]) )

  v_1 = v_1 + v_2 #Concatentate vertices
  return np.array(v_1), np.array(t_1)

def compute_and_display_patch( id_1 , id_2, adj_1, adj_2, matches_adj_adj, volume ):
  """ Equivalent to get_path, but it works with meshes represented as lists of 
      triangles and vertices. 

      This inconvinient, we should probably just convert the adjacent
      repretesentation to something that can be displayed.
      Look at get_vertices_triangles
  """

  patch_vertices = None; patch_triangles = None
  for vertex in matches_adj_adj:
    s_origin, s_slice = get_surrounding_vertex( vertex )
    vertices, triangles = marche_cubes( (id_1, id_2) , volume[s_slice] )
    if len(vertices) == 0:
      continue
    vertices = vertices + s_origin

    if patch_vertices == None:
      patch_vertices =  vertices
      patch_triangles = triangles
    else:
      patch_vertices, patch_triangles = merge_meshes(patch_vertices, patch_triangles,
                                                     vertices, triangles)

  display_marching_cubes(patch_vertices, patch_triangles , opacity = 0.4)

def get_surrounding_vertex( vertex ):
  
  slices = []
  origin = []
  for axis in vertex:
    if axis % 2 == 1:
      axis_slice = slice( axis/2 ,  axis/2 + 2 )
    else:
      axis_slice = slice( axis/2-1, axis/2 + 2)

    slices.append(axis_slice)
    origin.append(axis_slice.start * 2)

  return origin, tuple(slices)

def merge_adjacents(adj_1, adj_2):
  """ Given two meshes represented as adjacents (see get_adjacent),
      Return a new meshes containig both with the same repretesentation,
      without having duplicate vertices, because of the nature of the 
      datastructure.
  """

  if len(adj_1) > len(adj_2):
    adj_1, adj_2 = adj_2, adj_1
  for vertex in adj_1: #we don't have to check for existence because of using defaultdict(set)
    adj_2[vertex] = adj_2[vertex].union( adj_1[vertex])
  return adj_2

def find_displacements( adj, adj_patch, matches_adj_adj ):
  """
  """

  matches_adj_adj = set(matches_adj_adj)
  matches = find_matching_vertices(adj, adj_patch)
  if len(matches) == 0: #TODO it is strange that we don't find anything sometimes.
    # print 'there was no matching points between segment mesh and patch'
    return []

  magnitudes = []
  for vertex in matches:
    neighboors_to_consider = list(adj[vertex].difference( matches_adj_adj )
                             .union( adj_patch[vertex]))
    new_position = np.average( neighboors_to_consider , axis=0) 
    displacement =  new_position - vertex
    magnitude = np.linalg.norm(displacement)
    magnitudes.append(magnitude)
  return magnitudes

def compute_feature( adj_patch , adj_1 , adj_2):

  matches_adj_adj = find_matching_vertices(adj_1, adj_2)
  disp_1 = find_displacements(adj_1, adj_patch, matches_adj_adj)
  disp_2 = find_displacements(adj_2, adj_patch, matches_adj_adj)
  return np.average(disp_1), np.average(disp_2)


def display_marching_cubes(vertices, triangles, color=(0, 0, 0), opacity=1.0,  normals=None, display=True, show_vertices=False):
  """ Pushes meshes to renderer.
      remember to call mlab.show(), after everything 
      has being pushed.
  """

  if triangles == [] and show_vertices:
    for vertex in vertices:
      mlab.points3d(vertex[0], vertex[1], vertex[2], scale_factor=0.5, resolution=24, color=color)
  else:
    mesh = tvtk.PolyData(points=vertices, polys=triangles)
    surf = mlab.pipeline.surface(mesh, opacity=opacity, color=color)
    #mlab.pipeline.surface(mlab.pipeline.extract_edges(surf), color=color) show lines

  if normals != None:
    for i, vertex in enumerate(vertices):
      no = normals[ i ]  
      mlab.quiver3d(vertex[0], vertex[1], vertex[2],
                  no[0], no[1], no[2] 
                  ,scalars=(0.0))
  if display:
    mlab.show()
  

def display_pair( volume_id , id_1, id_2, matches):
  """ Given a volume_id, and two segments ids, it display both
      individual meshes, the mesh of the patch connecting them,
      and the displacemts vectors. Used for debugging.
  """

  vol = volume(volume_id , True)
  vol.getTile()

  vertices, triangles = marche_cubes( id_1 , vol.data )
  display_marching_cubes(vertices, triangles , color = (1.0,0.0,0.0), opacity=0.5)
  adj_1 =  get_adjacent( vertices, triangles )

  vertices, triangles = marche_cubes( id_2 , vol.data )
  display_marching_cubes(vertices, triangles , color = (0.0,0.0,1.0), opacity=0.5)
  adj_2 =  get_adjacent( vertices, triangles )

  matches_adj_adj = find_matching_vertices(adj_1, adj_2)
  compute_and_display_patch( id_1 , id_2, adj_1, adj_2, matches_adj_adj,  vol.data )

  adj_patch = get_patch( id_1 , id_2, adj_1, adj_2, matches_adj_adj, vol.data )
  disp_1 = find_displacements(adj_1, adj_patch, matches_adj_adj)
  disp_2 = find_displacements(adj_2, adj_patch, matches_adj_adj)

  #TODO display displacements
  matches = set(map( lambda tup: tuple([int(x * 2) for x in tup]), matches))
  matches_adj_adj = set(matches_adj_adj)
  for match in matches.union(matches_adj_adj):

    if match in matches and match in matches_adj_adj:
      color = (1.0,1.0,1.0)
    elif  match not in matches and match in matches_adj_adj:
      color = (0.0,0.0,1.0)
    else:
      color = (1.0,0.0,0.0)

    mlab.points3d(match[0], match[1], match[2], scale_factor=0.5, resolution=5 , color=color)
    #debug
    # mlab.quiver3d(vertex[0], vertex[1], vertex[2],
    #               patch_displacement[0], patch_displacement[1], patch_displacement[2] 
    #               ,scalars=(0.0))

    # sum_magnitude += np.linalg.norm(patch_displacement)
  mlab.show()
  return

def make_blob(verts, T):
  """Convert a list of tuples of numbers into a ctypes pointer-to-array"""
  size = len(verts) * len(verts[0])
  Blob = T * size
  floats = [c for v in verts for c in v]
  blob = Blob(*floats)
  return cast(blob, POINTER(T))
  
def vertices_triangles_to_openctm( vertices, triangles ):
  import ctypes 
  import openctm 


  if not vertices or not triangles:
    return ''

  pVertices = make_blob(vertices, ctypes.c_float)
  pTriangles = make_blob(triangles, ctypes.c_uint)
  pNormals = ctypesPOINTER(ctypes.c_float)()
  openctm.ctm = ctmNewContext(openctm.CTM_EXPORT)
  openctm.ctmDefineMesh(ctm, pVertices, len(vertices), pTriangles, len(triangles), pNormals)

  #Having to use a tmp file, because StringIO can't be easly pass
  #Because the biding is expecting an string
  #It is also possible to pass a c++ stream, but I don't know
  #how to interface that with python
  tf = tempfile.NamedTemporaryFile()
  openctm/ctmSave(ctm, tf.name)
  openctm.ctmFreeContext(ctm)
  s = tf.read()
  tf.close()
  return s

def export_mesh_as_threejs(vertices, triangles):

  vertices = vertices.astype('float')

  mesh = Trimesh(vertices = vertices, faces = triangles)
  mesh.fix_normals()

  #add column with zeros
  s = mesh.faces.shape
  faces = np.zeros(shape= (s[0], s[1]+1) )
  faces[:,1:4] = mesh.faces

  data = {
    "metadata": { "formatVersion" : 3 },    
    "vertices": list(mesh.vertices.reshape(-1)),
    "normals": list(mesh.vertex_normals.reshape(-1)),
    "faces": list(faces.reshape(-1))
    }

  
  return data

