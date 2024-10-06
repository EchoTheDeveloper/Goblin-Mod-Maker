import os
import shutil
import subprocess
import sys

def main():
    # Ask user for version number
    version = input("Enter the version number (e.g., 1.4.0): ").strip()

    # Define paths and variables
    source_dir = "."
    build_dir = os.path.join("bin", "build", version)
    dist_dir = os.path.join("bin", "dist", version)
    app_name = "Isle Goblin Mod Maker"
    icon_path = os.path.join("resources", "goblin-mod-maker.ico")
    resource_dir = os.path.join("resources")
    settings_file = "settings.json"
    legal_notice = "LEGAL-NOTICE.md"
    documentation = "DOCUMENTATION.md"
    main_script = "app.py"
    requirements_file = "requirements.txt"

    # Ensure build and dist directories exist
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(dist_dir, exist_ok=True)

    # Install dependencies if requirements.txt exists
    if os.path.exists(requirements_file):
        print(f"Installing dependencies from {requirements_file}...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "-r", requirements_file], capture_output=True)
        if result.returncode != 0:
            print("Error: Failed to install dependencies.")
            print(result.stderr.decode())
            sys.exit(1)
    else:
        print(f"Warning: {requirements_file} not found. Skipping dependency installation.")

    # Run PyInstaller to package the app
    print("Running PyInstaller to package the app...")
    pyinstaller_cmd = [
        "pyinstaller",
        "--onedir",
        f"--name={app_name}",
        f"--icon={icon_path}",
        f"--add-data={resource_dir};resources",
        f"--add-data={settings_file};.",
        f"--add-data={legal_notice};.",
        f"--add-data={documentation};.",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        "--noconfirm",
        main_script
    ]

    result = subprocess.run(pyinstaller_cmd, capture_output=True)
    if result.returncode != 0:
        print("Error: PyInstaller build failed.")
        print(result.stderr.decode())
        sys.exit(1)

    # Copy additional resources to the dist directory
    print("Copying additional resources...")
    shutil.copytree(resource_dir, os.path.join(dist_dir, "resources"), dirs_exist_ok=True)
    shutil.copy(settings_file, dist_dir)
    shutil.copy(legal_notice, dist_dir)
    shutil.copy(documentation, dist_dir)

    print(f"Build succeeded. The application is located in the {dist_dir} folder.")

if __name__ == "__main__":
    main()
