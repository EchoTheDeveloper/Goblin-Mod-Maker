from setuptools import setup

APP = ['isle-goblin-mod-maker.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['pygments', 'pyro', 'PIL'],
    'iconfile': 'resources/isle-goblin-mod-maker.ico',  # Replace with your icon file if needed
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)