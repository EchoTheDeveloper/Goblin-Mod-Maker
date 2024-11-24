import requests
import tkinter as tk
from tkinter import messagebox
import webbrowser
import pyro
import GraphicalInterface
import VERSION
import importlib
# URL to fetch the latest version
url = 'https://raw.githubusercontent.com/EchoTheDeveloper/Goblin-Mod-Maker/refs/heads/main/LATEST_VERSION'

def check_version():
    try:
        # Fetch the latest version from the URL
        response = requests.get(url)
        response.raise_for_status()

        latest_version = response.text.strip()

        # Update LATEST_VERSION in the VERSION.py file
        with open("VERSION.py", "r") as version_file:
            lines = version_file.readlines()

        with open("VERSION.py", "w") as version_file:
            for line in lines:
                if line.startswith("LATEST_VERSION ="):
                    version_file.write(f'LATEST_VERSION = "{latest_version}"\n')
                else:
                    version_file.write(line)
        importlib.reload(VERSION)
        
        if VERSION.CURRENT_VERSION < latest_version:
            # Create a Tkinter window to prompt for update
            root = tk.Tk()
            root.withdraw()  # Hide the root window

            # Show message box to ask the user whether they want to update
            answer = messagebox.askyesno(
                "Update Available",
                f"An update is available.\nCurrent Version: {VERSION.CURRENT_VERSION}, Latest Version: {latest_version}\nDo you want to update?"
            )

            if answer:
                # Open the update link in the web browser
                webbrowser.open("https://echothedeveloper.itch.io/gmm")
            else:
                root.destroy()

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the latest version: {e}")

    interface()

def interface():
    # Start the graphical interface if no update is required
    GraphicalInterface.InterfaceMenu()

if __name__ == "__main__":
    check_version()  # Perform version check before starting the interface
    pyro.mainloop()
