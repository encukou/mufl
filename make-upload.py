from pathlib import Path
import tempfile
import shutil
import subprocess
import sys
import zipfile

def ignore(f, contents):
    #print(f, contents)
    return ('__pycache__')

needed_files = [
    'README.md', 'LICENSE.MIT',
    'requirements.txt', 'requirements.in',
    'pics.svg', 'pics.png', 'island_shadow.xcf',
    'run_game.py', 'install_and_run.py',
]

KNOWN_BINARY = [
    'glcontext==2.2.0',
    'mapbox-earcut==0.12.10',
    'moderngl==5.6.2',
    'numpy==1.17.5',
    'Pillow==7.2.0',
    'pygame==2.0.0.dev10',
]

with tempfile.TemporaryDirectory() as _tmpdir:
    tmpdir = Path(_tmpdir)
    shutil.copytree('mufl', tmpdir/'mufl', ignore=ignore)
    for filename in needed_files:
        print(filename )
        shutil.copy(filename, tmpdir/filename)

    for req in Path('requirements.txt').read_text().splitlines():
        if req and req not in KNOWN_BINARY:
            subprocess.run([
                'pip', 'install', '-t', tmpdir/'vendor',
                '--abi', 'missing',
                '--implementation', 'missing',
                '--no-deps', '--no-compile',
                '--only-binary=:all:',
                req,
            ], check=True)
    subprocess.run(['tree', tmpdir])

    zipf = zipfile.ZipFile('mufl-castaway.zip', 'w')
    for p in tmpdir.glob('**/*'):
        rel = 'mufl-castaway' / p.relative_to(tmpdir)
        print(p, rel)
        zipf.write(p, rel)

    subprocess.run([sys.executable, 'install_and_run.py'], cwd=tmpdir)
