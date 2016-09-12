
class Classifier(object):
  def __init__(self):
    pass  

  def train(self, examples):
    pass

  def report(self, examples):
    pass


class Oracle(Classifier):
  def pred(self, features):
    return features['soft_label']


class MeanOracle(Classifier):
  """
  Merge in the ordered dictated by mean affinity
  But only the objects that are correct.
  """ 
  def pred(self, features):
    if features['soft_label'] > 0.5:
      return features['mean_affinity']
    return 0.0