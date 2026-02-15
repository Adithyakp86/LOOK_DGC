import os
import sys
import subprocess

os.chdir(os.path.join(os.path.dirname(__file__), 'gui'))
subprocess.run([sys.executable, 'look-dgc.py'])
