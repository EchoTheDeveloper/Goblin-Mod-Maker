import requests
import tkinter as tk
from tkinter import messagebox
import webbrowser
import pyro
import GraphicalInterface

# URL to fetch the latest version
url = 'https://raw.githubusercontent.com/EchoTheDeveloper/Goblin-Mod-Maker/refs/heads/main/LATEST_VERSION'

# Define the current version
CURRENT_VERSION = "v1.4.0"

def check_version():
    try:
        # Fetch the latest version from the URL
        response = requests.get(url)
        response.raise_for_status()

        latest_version = response.text.strip()

        # Check if the current version is the same as the latest version
        if CURRENT_VERSION < latest_version:
            # Create a Tkinter window to prompt for update
            root = tk.Tk()
            root.withdraw()  # Hide the root window

            # Show message box to ask the user whether they want to update
            answer = messagebox.askyesno(
                "Update Available",
                f"An update is available.\nCurrent Version: {CURRENT_VERSION}, Latest Version: {latest_version}\nDo you want to update?"
            )

            if answer:
                # Open the update link in the web browser
                webbrowser.open("https://echothedeveloper.itch.io/gmm")
            else:
                root.destroy()
                interface()
        else:
            interface()

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the latest version: {e}")
        interface()

def interface():
    # Start the graphical interface if no update is required
    GraphicalInterface.InterfaceMenu()

if __name__ == "__main__":
    check_version()  # Perform version check before starting the interface
    pyro.mainloop()
