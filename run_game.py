import sys
import os
from pathlib import Path

os.chdir(Path(__file__).parent)
sys.path.insert(0, 'vendor')

from mufl import run

run()
