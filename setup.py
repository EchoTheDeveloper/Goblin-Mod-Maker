####### THIS IS OBSOLETE AND WILL BE REPLACE WHEN WE SWITCH TO PYINSTALLER FOR THE NEXT VERSION

"""
from cx_Freeze import setup, Executable
import os

# Define the application version
version = "1.0.1"

# Define the target executable
executables = [
    Executable(
        "app.py",
        base=None,
        target_name="IsleGoblinModMaker"
    )
]

# Define the build options
build_options = {
    "packages": ["PIL", "pygments", "pyroprompt", "pyro"],  # List of packages to include
    "excludes": [],  # List of packages to exclude if needed
    "include_files": [
        ("resources/", "resources/"),  # Include the 'resources' folder in the build
        ("settings.json", "settings.json")  # Ensure settings file is included
    ],
    "optimize": 2,  # Optimization level
}

# Setup configuration
setup(
    name="Isle Goblin Mod Maker",
    version=version,
    description="Isle Goblin Mod Maker Application",
    options={"build_app": build_options},
    executables=executables,
)
"""
