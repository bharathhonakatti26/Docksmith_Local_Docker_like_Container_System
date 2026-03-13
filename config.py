import os

HOME = os.path.expanduser('~')
DOCKSMITH_DIR = os.path.join(HOME, '.docksmith')
IMAGES_DIR = os.path.join(DOCKSMITH_DIR, 'images')
LAYERS_DIR = os.path.join(DOCKSMITH_DIR, 'layers')
CACHE_DIR = os.path.join(DOCKSMITH_DIR, 'cache')
REGISTRY_DIR = os.path.join(HOME, '.docksmith_registry')

for d in [DOCKSMITH_DIR, IMAGES_DIR, LAYERS_DIR, CACHE_DIR, REGISTRY_DIR]:
    os.makedirs(d, exist_ok=True)
