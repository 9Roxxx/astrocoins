import os
import sys

from astrocoins.wsgi import application

# Путь к виртуальному окружению (для Windows)
import os
venv_path = os.path.join(os.path.dirname(__file__), 'env_new', 'Lib', 'site-packages')
if venv_path not in sys.path:
    sys.path.insert(0, venv_path)

# Путь к проекту
project_path = os.path.dirname(__file__)
if project_path not in sys.path:
    sys.path.insert(0, project_path)