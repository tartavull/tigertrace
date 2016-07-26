from .task import Agglomeration
from .ingest import Ingest
from .construct import Construct
from .evaluate import Evaluate
from .collapse import Collapse
from .export import Export
from .train import Train

tasks_dict = { 'Ingest': Ingest,
               'Construct': Construct,
               'Evaluate': Evaluate,
               'Collapse': Collapse,
               'Export': Export,
               'Train': Train
              }