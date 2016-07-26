"""
Binary tree.
Keys are not ordered in any way
"""

class BinaryTree(object):

  def __init__(self, key=0, fromarray=None):
    self.left = None
    self.right = None
    self.parent = None
    self.key = key

    if fromarray:
      self.key = fromarray[0]
      self.read_array(array=fromarray)

  def read_array(tree , array , parent_pos=0):
    def left_pos(parent_pos):
      return (parent_pos  + 1 ) * 2 - 1
    def right_pos(parent_pos):
      return (parent_pos + 1) * 2

    try:
      left_key = array[left_pos(parent_pos)]
      if left_key != -1:
        tree.left = BinaryTree(left_key)
        tree.left.read_array(array, parent_pos=left_pos(parent_pos))
    except IndexError:
      pass

    try:
      right_key = array[right_pos(parent_pos)]
      if right_key != -1:
        tree.right = BinaryTree(right_key)
        tree.right.read_array(array, parent_pos=right_pos(parent_pos))
    except IndexError:
      pass

  def __eq__(self, other):
    if type(self) != type(other):
      return False

    return self.key == other.key and self.left == other.left and self.right == other.right

  def insert_left_tree(self, tree):
    self.left = tree
    self.left.parent = self
    return self

  def insert_right_tree(self, tree):
    self.right = tree
    self.right.parent = self
    return self

  def insert_left_leaf(self, leaf_key):
    self.left = BinaryTree(leaf_key)
    self.left.parent = self
    return self
    
  def insert_right_leaf(self, leaf_key):
    self.right = BinaryTree(leaf_key)
    self.right.parent = self
    return self

  def __str__(self):
    def recurse(node):
      if node is None: return [], 0, 0
      label = str(node.key)
      left_lines, left_pos, left_width = recurse(node.left)
      right_lines, right_pos, right_width = recurse(node.right)
      middle = max(right_pos + left_width - left_pos + 1, len(label), 2)
      pos = left_pos + middle // 2
      width = left_pos + middle + right_width - right_pos
      while len(left_lines) < len(right_lines):
          left_lines.append(' ' * left_width)
      while len(right_lines) < len(left_lines):
          right_lines.append(' ' * right_width)
      if (middle - len(label)) % 2 == 1 and node.parent is not None and \
         node is node.parent.left and len(label) < middle:
          label += '.'
      label = label.center(middle, '.')
      if label[0] == '.': label = ' ' + label[1:]
      if label[-1] == '.': label = label[:-1] + ' '
      lines = [' ' * left_pos + label + ' ' * (right_width - right_pos),
               ' ' * left_pos + '/' + ' ' * (middle-2) +
               '\\' + ' ' * (right_width - right_pos)] + \
        [left_line + ' ' * (width - left_width - right_width) +
         right_line
         for left_line, right_line in zip(left_lines, right_lines)]
      return lines, pos, width
    return '\n'.join(recurse(self)[0]) + '\n\n'

  def  __repr__(self):
    return 'BinaryTree(\n{}\n)'.format(self.__str__()) 

  def get_leaf(self):
    if self.left:
      return self.left.get_leaf()
    if self.right:
      return self.right.get_leaf()
    return self.key

  def get_leaf_stack(self):
    node = self
    while True:
      if node.left is not None:
        node = node.left
        continue
      elif node.right is not None:
        node = node.right
        continue
      else:
        return node.key

  def get_all_leafs(self):
    leafs = []
    stack = [self]
    while True:
      try:
        node = stack.pop()
      except IndexError:
        return leafs

      if node.left is None and node.right is None:
        leafs.append(node.key)
        continue
      if node.left is not None:
        stack.append(node.left)
      if node.right is not None:
        stack.append(node.right)
      