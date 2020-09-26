import sys

if sys.version_info < (3, 8):
    exit('This game requires Python 3.8+')

import os
from pathlib import Path
import subprocess

HERE = Path(__file__).parent
venv_path = HERE / 'venv'

possible_python_locations = 'bin/python', 'scripts/python'

def run(args, **kwargs):
    kwargs.setdefault('check', True)
    print('Running:', ' '.join(str(s) for s in args))
    subprocess.run(args, **kwargs)

if not venv_path.exists():
    run([sys.executable, '-m', 'venv', venv_path])

for loc in possible_python_locations:
    interp_path = venv_path / loc
    if interp_path.exists():
        break
else:
    exit('Could not find Python in virtualenv :(')

environ = dict(os.environ)
environ['PYTHONPATH'] = 'vendor'

reqs = Path('requirements.txt').read_text().splitlines()
run([interp_path, '-m', 'pip', 'install', '--no-deps', *reqs], env=environ)
run([interp_path, '-m', 'pip', 'check'], env=environ, check=False)

run([interp_path, '-m', 'mufl'], env=environ)

