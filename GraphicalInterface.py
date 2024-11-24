"""
This module is the main module of the entire program, running this file is how you start the application
It contains the code for the main menu which is what you are greeted with when you are using the program
"""

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from tkinter import messagebox, filedialog
from tkinter import *
from PIL import ImageTk, Image
from functools import partial
from pygame import mixer
import json
import webbrowser
try:
    import winreg
except:
    import plistlib

from pygments.lexers.dotnet import CSharpLexer
import pyroprompt

# Makes it easier to make a prompt
create_prompt = pyroprompt.create_prompt
from os.path import exists
from ModObject import *
import pyro
import shutil
# keep track of the number of windows so you only open the main menu when the last one is closed
window_count = 0
# keep track of whether it should even open the main menu depending on if there is one already open (avoid more than one
# menu open at a time
can_make_menu = True

DEFAULT_SETTINGS = {
    "Default Game": "Isle Goblin",
    "Default Game Folder": "Isle Goblin Playtest",
    "Default Steam Directory": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\",
    "Show Line Numbers": True,
    "Selected Theme": "Isle Goblin",
    "Selected Code Font": "JetBrainsMono.ttf"
}

# These two functions are used to keep track of how many pyro windows are open becuase the main interface should open
# when the last window is closed but not when just any window is closed

def set_window_count(x):
    global window_count
    window_count = x


def get_window_count():
    global window_count
    return window_count

# This is a function that gets called when the main window gets closed, it sets can_make_menu to True because now a new
# menu can be made without having duplicates
def close(menu, end=True):
    global can_make_menu
    can_make_menu = True
    try:
        menu.root.destroy()
    except TclError:
        pass

def load_theme(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return data

def load_settings():
    with open("settings.json", 'r') as file:
        data = json.load(file)
    return data
settings = load_settings()
theme_data = load_theme('resources/themes/' + settings.get("Selected Theme", "Isle Goblin") + ".json")

InterfaceMenu_Background = theme_data.get("interfacemenu", {}).get("background", "")
InterfaceMenu_Geometry = theme_data.get("interfacemenu", {}).get("geometry", "")
InterfaceMenu_NewButtonBackground = theme_data.get("interfacemenu", {}).get("newbuttonbackground", "")
InterfaceMenu_OpenButtonBackground = theme_data.get("interfacemenu", {}).get("openbuttonbackground", "")
InterfaceMenu_MouseEnter = theme_data.get("interfacemenu", {}).get("mouseenter", "")
InterfaceMenu_MouseExit = theme_data.get("interfacemenu", {}).get("mouseexit", "")

InterfaceMenu_ButtonConfigFG = theme_data.get("buttonconfig", {}).get("foreground", "")
InterfaceMenu_ButtonConfigBG = theme_data.get("buttonconfig", {}).get("background", "")

PyroPrompt_Background = theme_data.get("pyroprompt", {}).get("background", "")
PyroPrompt_Foreground = theme_data.get("pyroprompt", {}).get("foreground", "")
PyroPrompt_WarningTextColor = theme_data.get("pyroprompt", {}).get("warningtextcolor", "")

NewButton = theme_data.get("newbutton", "")
OpenButton = theme_data.get("openbutton", "")

Click = theme_data.get("click", "")
Hover = theme_data.get("hover", "")

class InterfaceMenu:

    def __init__(self):
        # doesn't make a menu if can_make_menu is false, meaning there is a menu already open
        global can_make_menu
        if not can_make_menu:
            return
        # it sets can_make_menu to false because now there is a menu and a new one shouldn't be made
        can_make_menu = False
        self.settings = self.find_settings()
        # Setting up the main window visuals
        #STUFF
        theme_data = load_theme('resources/themes/' + self.settings.get("Selected Theme", "Isle Goblin") + ".json") 
        # Update the theme settings
        global InterfaceMenu_Background, InterfaceMenu_Geometry, InterfaceMenu_NewButtonBackground, InterfaceMenu_OpenButtonBackground
        global InterfaceMenu_MouseEnter, InterfaceMenu_MouseExit, InterfaceMenu_ButtonConfigFG, InterfaceMenu_ButtonConfigBG
        global PyroPrompt_Background, PyroPrompt_Foreground, PyroPrompt_WarningTextColor
        global NewButton, OpenButton
        global Click, Hover
        
        InterfaceMenu_Background = theme_data.get("interfacemenu", {}).get("background", "")
        InterfaceMenu_Geometry = theme_data.get("interfacemenu", {}).get("geometry", "")
        InterfaceMenu_NewButtonBackground = theme_data.get("interfacemenu", {}).get("newbuttonbackground", "")
        InterfaceMenu_OpenButtonBackground = theme_data.get("interfacemenu", {}).get("openbuttonbackground", "")
        InterfaceMenu_MouseEnter = theme_data.get("interfacemenu", {}).get("mouseenter", "")
        InterfaceMenu_MouseExit = theme_data.get("interfacemenu", {}).get("mouseexit", "")
        InterfaceMenu_ButtonConfigFG = theme_data.get("buttonconfig", {}).get("foreground", "")
        InterfaceMenu_ButtonConfigBG = theme_data.get("buttonconfig", {}).get("background", "")
        PyroPrompt_Background = theme_data.get("pyroprompt", {}).get("background", "")
        PyroPrompt_Foreground = theme_data.get("pyroprompt", {}).get("foreground", "")
        PyroPrompt_WarningTextColor = theme_data.get("pyroprompt", {}).get("background", "")
        NewButton = theme_data.get("newbutton", "")
        OpenButton = theme_data.get("openbutton", "")
        Click = theme_data.get("click", "")
        Hover = theme_data.get("hover", "")
        #STUFF
        self.root = Tk()
        mixer.init()
        self.root.configure(background=InterfaceMenu_Background)
        self.root.geometry(InterfaceMenu_Geometry)
        self.root.resizable(0, 0)
        self.root.title("Goblin Mod Maker - Main Menu")
        self.root.iconbitmap("resources/goblin-mod-maker.ico")
        self.new_image = PhotoImage(file=NewButton)
        self.open_image = PhotoImage(file=OpenButton)
        self.new_button = Label(self.root, image=self.new_image, background=InterfaceMenu_NewButtonBackground)
        self.open_button = Label(self.root, image=self.open_image, background=InterfaceMenu_OpenButtonBackground)
        self.new_button.place(x=20, y=20)
        self.open_button.place(x=240, y=20)
        # The buttons are bound to the self.new function and self.load function because they are new and load buttons
        self.new_button.bind("<Button-1>", self.new)
        self.open_button.bind("<Button-1>", self.load)
        
        def new_button_hover_enter(e):
            self.new_button.config(borderwidth=10, highlightbackground=InterfaceMenu_MouseEnter)
            try:
                mixer.music.load(Hover)
                mixer.music.play(loops=0)
            except:
                pass

        def new_button_hover_exit(e):
            self.new_button.config(borderwidth=0, highlightbackground=InterfaceMenu_NewButtonBackground)

        def open_button_hover_enter(e):
            self.open_button.config(borderwidth=10, highlightbackground=InterfaceMenu_MouseEnter)
            # PlaySound(Hover, SND_FILENAME)
            try:
                mixer.music.load(Hover)
                mixer.music.play(loops=0)
            except:
                pass
            
        def open_button_hover_exit(e):
            self.open_button.config(borderwidth=0,highlightbackground=InterfaceMenu_OpenButtonBackground)
        
        with open('settings.json', 'w') as json_file:
            json.dump(self.settings, json_file, indent=4)
        self.extra_buttons = []

        self.open_external = Label(self.root, text="Open From Goblin Mod Maker (.gmm) File")
        self.open_external.place(x=20, y=150)
        self.open_external.bind("<Button-1>", self.open_dialog)
        self.extra_buttons.append(self.open_external)

        self.settings_button = Label(self.root, text="Open GMM Settings")
        self.settings_button.place(x=20, y=180)
        self.settings_button.bind("<Button-1>", self.open_settings_window)
        self.extra_buttons.append(self.settings_button)

        # self.convert_mod = Label(self.root, text="Convert .igmm/.umm to .gmm")
        # self.convert_mod.place(x=20, y=210)
        # self.convert_mod.bind("<Button-1>", self.convert_prompt)
        # self.extra_buttons.append(self.convert_mod)
        self.more_options = Label(self.root, text="More Options")
        self.more_options.place(x=20, y=210)
        self.more_options.bind("<Button-1>", self.more_options_prompt)
        self.extra_buttons.append(self.more_options)
        
        from VERSION import CURRENT_VERSION, LATEST_VERSION
        if (CURRENT_VERSION < LATEST_VERSION):
            self.update_btn = Label(self.root, text="Update GMM")
            self.update_btn.place(x=350, y=210)
            self.update_btn.bind("<Button-1>", self.open_update_link)
            self.extra_buttons.append(self.update_btn)
        
        
        for button in self.extra_buttons:
            button.config(font=("Calibri", 15), fg=InterfaceMenu_ButtonConfigFG, background=InterfaceMenu_Background)
            button.bind("<Enter>", self.mouse_enter)
            button.bind("<Leave>", self.mouse_exit)

        self.new_button.bind("<Enter>", new_button_hover_enter)
        self.new_button.bind("<Leave>", new_button_hover_exit)
        self.open_button.bind("<Enter>", open_button_hover_enter)
        self.open_button.bind("<Leave>", open_button_hover_exit)
        
        foldername = self.settings.get("Default Game Folder", "")
        steampath = self.settings.get("Default Steam Directory", "")
        try:
            if not os.path.isdir(os.path.join(steampath, foldername)):
                # Try to find the correct Steam directory
                steam_path = find_steam_directory(foldername)
                if not steam_path:
                    messagebox.showerror("Game Not Found",
                                        f"Game Not Found. There is no directory \"{os.path.join(steam_path, foldername)}\"",
                                        parent=self)
                    return False
                with open("settings.json", 'r') as file:
                    settings = json.load(file)
                
                settings["Default Steam Directory"] = steam_path
                
                with open("settings.json", 'w') as file:
                    json.dump(settings, file, indent=4)
        except:
            pass
                
        # theme_data = load_theme('resources/themes/' + self.settings.get("Selected Theme", "Isle Goblin") + ".json")
            
        # Update the theme settings
        
        self.root.configure(background=InterfaceMenu_Background)
        self.new_button.config(background=InterfaceMenu_NewButtonBackground)
        self.open_button.config(background=InterfaceMenu_OpenButtonBackground)
        self.new_image.config(file=NewButton)
        self.open_image.config(file=OpenButton)
        
        for button in self.extra_buttons:
            button.config(fg=InterfaceMenu_ButtonConfigFG, background=InterfaceMenu_Background)

        # Instead of doing root.mainloop we do pyro.add_window to avoid thread conflicts, pyro deals with calling
        # root.update() on  everything in the pyro window list, there is also no need to remove closed windows from this
        pyro.add_window(self.root)

    def open_update_link(self, e=None):
        webbrowser.open("https://echothedeveloper.itch.io/gmm")
        
    def more_options_prompt(self, e=None):
        try:
            mixer.music.load(Click)
            mixer.music.play(loops=0)
        except:
            pass
        title = "More Options"
        window = Toplevel(self.root)
        window.title(title)
        
        Frame(window, width=500, background=PyroPrompt_Background).pack()
        frame = Frame(window, width=500, background=PyroPrompt_Background)
        frame.pack(fill="x")
        
        heading = Label(frame, text=title, font=("Calibri", 18), background=PyroPrompt_Background, fg=PyroPrompt_Foreground)
        heading.pack(fill="x", pady=10)
        
        window.configure(background=PyroPrompt_Background)
        window.resizable(0, 0)
        window.iconbitmap("resources/goblin-mod-maker.ico")
        
        labels = []

        # Methods
        def close_window():
            window.destroy()

        # Options
        button_frame = Frame(window, background=PyroPrompt_Background, padx=10, pady=10)
        button_frame.pack(expand=True)  # Center the button frame
        
        self.convert_mod = Label(button_frame, text="Convert .igmm/.umm to .gmm")
        self.convert_mod.bind("<Button-1>", self.convert_prompt)
        labels.append(self.convert_mod)

        self.import_projects_label = Label(button_frame, text="Import Projects")
        self.import_projects_label.bind("<Button-1>", self.import_projects)
        labels.append(self.import_projects_label)

        # Style Buttons
        for button in labels:
            button.config(font=("Calibri", 15), fg=InterfaceMenu_ButtonConfigFG, background=InterfaceMenu_Background)
            button.pack(pady=(10, 10))  # Add padding for spacing
            button.bind("<Enter>", self.mouse_enter)
            button.bind("<Leave>", self.mouse_exit)

        # Close button
        buttons = Frame(window, background=PyroPrompt_Background)
        buttons.pack(pady=(10, 10))  # Add padding for spacing
        Button(buttons, text="Close", bg=PyroPrompt_Background, fg=PyroPrompt_Foreground, command=close_window).pack(pady=(5, 5))  # Center the close button

    def import_projects(self, e):
        folder = filedialog.askdirectory(title="Select Old Goblin Mod Maker Folder", initialdir=os.getcwd())
        if folder is None: 
            return
        project_folder_path = os.path.join(folder, "projects")
        print(project_folder_path)
        if not os.path.exists(project_folder_path):
            messagebox.showerror("Projects folder not found", "The directory provided has no \"projects\" folder")
            return
        
        current_projects_path = os.path.join(os.getcwd(), "projects")
        os.makedirs(current_projects_path, exist_ok=True)
        
        if (folder):
            try:
                
                for item in os.listdir(project_folder_path):
                    source_path = os.path.join(project_folder_path, item)
                    destination_path = os.path.join(current_projects_path, item)
                    if not os.path.exists(destination_path):
                        if os.path.isdir(source_path):
                            shutil.copytree(source_path, destination_path)
                        else:
                            shutil.copy2(source_path, destination_path)

                messagebox.showinfo("Import Successful", "Projects imported successfully.")
            except Exception as error:
                messagebox.showerror("Error", f"An error occurred while importing projects: {error}")
        
    def convert_prompt(self, e):
        file = filedialog.askopenfile(title="Select the mod to open", initialdir=os.getcwd(), filetypes=[("Isle Goblin Mod Maker File", "*.igmm"), ("Unity Mod Maker File", "*.umm")])
        if file is None: return # If file is Null then cancel
        isInProjects = messagebox.askyesno("Add to Projects Folder", "Would you like to add this mod to the projects folder? \n Keep in mind that most of these files won't be compatible")
        
        old_file_path = file.name
        file_name = os.path.basename(old_file_path).rsplit(".", 1)[0]
        if file_name.endswith("-auto"): # They may have opened an autosave file so this is a 
            file_name = file_name[:-5]  # way to get rid of that -auto that would get put on at the end
            
        file.close()
        if isInProjects:
            projects_folder = os.path.join(os.getcwd(), "projects")
            os.makedirs(projects_folder, exist_ok=True)

            project_folder = os.path.join(projects_folder, file_name)
            os.makedirs(project_folder, exist_ok=True)

            new_file_path = os.path.join(project_folder, file_name + ".gmm")
        else:
            new_file_path = old_file_path.rsplit(".", 1)[0] + ".gmm"
        os.rename(old_file_path, new_file_path)
        messagebox.showinfo("Successful", "Mod successfully converted.")


    def mouse_enter(self, e):
        e.widget.config(borderwidth=5, fg=InterfaceMenu_MouseEnter)
        try:
            mixer.music.load(Hover)
            mixer.music.play(loops=0)
        except:
            pass
    def mouse_exit(self, e):
        e.widget.config(borderwidth=0, fg=InterfaceMenu_MouseExit)


    def find_settings(self):
        settings = None
        try:
            with open('settings.json') as json_file:
                settings = json.load(json_file)
                for item in DEFAULT_SETTINGS:
                    if item not in settings:
                        settings[item] = DEFAULT_SETTINGS[item]
            with open('settings.json', 'w') as json_file:
                json.dump(settings, json_file, indent=4)
        except Exception:
            with open('settings.json', 'w') as json_file:
                json.dump(DEFAULT_SETTINGS, json_file, indent=4)
                settings = DEFAULT_SETTINGS
        return settings

    def open_settings_window(self, event=None):
        try:
            mixer.music.load(Click)
            mixer.music.play(loops=0)
        except:
            pass
        title = "Goblin Mod Maker Settings"
        settings_window = Toplevel(self.root)
        settings_window.title(title)
        Frame(settings_window, width=500, background=PyroPrompt_Background).pack()
        frame = Frame(settings_window, width=500, background=PyroPrompt_Background)
        frame.pack(fill="x")
        heading = Label(frame, text=title, font=("Calibri", 18), background=PyroPrompt_Background, fg=PyroPrompt_Foreground)
        heading.pack(fill="x", pady=10)
        settings_window.configure(background=PyroPrompt_Background)
        settings_window.resizable(0, 0)
        settings_window.iconbitmap("resources/goblin-mod-maker.ico")
        
        global settings 
        settings = self.find_settings() #reload the settings
        
        foldername = self.settings.get("Default Game Folder", "")
        steampath = self.settings.get("Default Steam Directory", "")            

        Label(settings_window, background=PyroPrompt_Background, fg=PyroPrompt_Foreground, font=("Calibri", 12), text="Default Game Folder").pack(fill="x", padx=10)
        game_folder_entry = Entry(settings_window, background=PyroPrompt_Background, fg=PyroPrompt_Foreground, font=("Calibri", 12))
        game_folder_entry.insert(0, self.settings.get("Default Game Folder", ""))
        game_folder_entry.pack(fill="x", padx=10, pady=10)

        steam_path = find_steam_directory(self.settings.get("Default Game Folder", ""))
        
        steamdir = Frame(settings_window, background=PyroPrompt_Background)
        steamdir.pack()
        Label(steamdir, background=PyroPrompt_Background, fg=PyroPrompt_Foreground, font=("Calibri", 12), text="Default Steam Directory").grid(row=0, column=1, padx=10, pady=(10, 10))
        
        steam_dir_entry = Entry(settings_window, background=PyroPrompt_Background, fg=PyroPrompt_Foreground, font=("Calibri", 12))
        steam_dir_entry.insert(0, self.settings.get("Default Steam Directory", steam_path))
        steam_dir_entry.pack(fill="x", padx=10, pady=10)
        
        # Function to auto-find the Steam directory
        def auto_find_steam_directory():
            foldername = self.settings.get("Default Game Folder", "")
            steampath = self.settings.get("Default Steam Directory", "")
            if not os.path.isdir(os.path.join(steampath, foldername)):
                # Try to find the correct Steam directory
                steam_path = find_steam_directory(foldername)
                if not steam_path:
                    messagebox.showerror("Game Not Found",
                                        f"Game Not Found. There is no directory \"{os.path.join(steam_path, foldername)}\"",
                                        parent=self)
                    return False
                with open("settings.json", 'r') as file:
                    settings = json.load(file)
                
                settings["Default Steam Directory"] = steam_path
                
                with open("settings.json", 'w') as file:
                    json.dump(settings, file, indent=4)
                steam_dir_entry.delete(0, "end")
                steam_dir_entry.insert(0, steam_path)
            elif steampath == find_steam_directory(foldername):
                messagebox.showinfo("Steam Directory Already Set", "The correct Steam directory has already been set.")
            else:
                messagebox.showwarning("Something went wrong :(", f"Directory {os.path.join(steampath, foldername)} does not exist.")
            settings_window.focus()

        if not os.path.isdir(os.path.join(steampath, foldername)):
            auto_find_steam_directory()

        Button(steamdir, text="Auto Find Steam Directory", bg=PyroPrompt_Background, fg=PyroPrompt_Foreground, command=auto_find_steam_directory).grid(row=0, column=2, padx=10, pady=(10, 10))

        theme_folder = "resources/themes"
        themes = [os.path.splitext(file)[0] for file in os.listdir(theme_folder) if file.endswith(".json")]

        # Default selection for the dropdown
        clicked = StringVar()
        clicked.set(self.settings.get("Selected Theme", "Isle Goblin"))  # Set the last selected theme or to Default

        Label(settings_window, background=PyroPrompt_Background, fg=PyroPrompt_Foreground, font=("Calibri", 12), text="Select Theme").pack(fill="x", padx=10)
        themeDrop = OptionMenu(settings_window, clicked, *themes)
        themeDrop.config(bg=PyroPrompt_Background, fg=PyroPrompt_Foreground)
        themeDrop["menu"].config(bg=PyroPrompt_Background, fg=PyroPrompt_Foreground)
        themeDrop.pack(fill="x", padx=10, pady=10)

        font_folder = "resources/fonts"
        fonts = [os.path.splitext(f)[0] for f in os.listdir(font_folder) if f.endswith('.ttf')]

        selected_font = StringVar()
        selected_font.set(self.settings.get("Selected Code Font", "JetBrainsMono"))  # Set default font without extension

        Label(settings_window, background=PyroPrompt_Background, fg=PyroPrompt_Foreground, font=("Calibri", 12), text="Select Code Font").pack(fill="x", padx=10)
        fontDrop = OptionMenu(settings_window, selected_font, *fonts)
        fontDrop.config(bg=PyroPrompt_Background, fg=PyroPrompt_Foreground)
        fontDrop["menu"].config(bg=PyroPrompt_Background, fg=PyroPrompt_Foreground)
        fontDrop.pack(fill="x", padx=10, pady=10)

        show_line_numbers_var = BooleanVar()
        show_line_numbers_var.set(self.settings.get("Show Line Numbers", True))  # Default to True if not found
        show_line_numbers_check = Checkbutton(settings_window, background=PyroPrompt_Background, fg=PyroPrompt_Foreground, font=("Calibri", 12), 
                                            text="Show Line Numbers", variable=show_line_numbers_var)
        show_line_numbers_check.pack(padx=10, pady=10)

        # Save the updated settings when the "Done" button is clicked
        def save_settings():
            # Update the settings dictionary with the new values
            self.settings["Default Game Folder"] = game_folder_entry.get()
            self.settings["Default Steam Directory"] = steam_dir_entry.get()
            self.settings["Show Line Numbers"] = show_line_numbers_var.get()
            self.settings["Selected Theme"] = clicked.get()
            self.settings["Selected Code Font"] = selected_font.get()  # Save selected font
            
            # Save the settings to the JSON file
            with open('settings.json', 'w') as json_file:
                json.dump(self.settings, json_file, indent=4)

            # Reload the theme
            theme_data = load_theme('resources/themes/' + self.settings.get("Selected Theme", "Isle Goblin") + ".json")
            
            # Update the theme settings
            global InterfaceMenu_Background, InterfaceMenu_Geometry, InterfaceMenu_NewButtonBackground, InterfaceMenu_OpenButtonBackground
            global InterfaceMenu_MouseEnter, InterfaceMenu_MouseExit, InterfaceMenu_ButtonConfigFG, InterfaceMenu_ButtonConfigBG
            global PyroPrompt_Background, PyroPrompt_Foreground, PyroPrompt_WarningTextColor
            global NewButton, OpenButton
            global Click, Hover
            try:
                mixer.music.load(Click)
                mixer.music.play(loops=0)
            except:
                pass
            
            InterfaceMenu_Background = theme_data.get("interfacemenu", {}).get("background", "")
            InterfaceMenu_Geometry = theme_data.get("interfacemenu", {}).get("geometry", "")
            InterfaceMenu_NewButtonBackground = theme_data.get("interfacemenu", {}).get("newbuttonbackground", "")
            InterfaceMenu_OpenButtonBackground = theme_data.get("interfacemenu", {}).get("openbuttonbackground", "")
            InterfaceMenu_MouseEnter = theme_data.get("interfacemenu", {}).get("mouseenter", "")
            InterfaceMenu_MouseExit = theme_data.get("interfacemenu", {}).get("mouseexit", "")

            InterfaceMenu_ButtonConfigFG = theme_data.get("buttonconfig", {}).get("foreground", "")
            InterfaceMenu_ButtonConfigBG = theme_data.get("buttonconfig", {}).get("background", "")

            PyroPrompt_Background = theme_data.get("pyroprompt", {}).get("background", "")
            PyroPrompt_Foreground = theme_data.get("pyroprompt", {}).get("foreground", "")
            PyroPrompt_WarningTextColor = theme_data.get("pyroprompt", {}).get("background", "")

            NewButton = theme_data.get("newbutton", "")
            OpenButton = theme_data.get("openbutton", "")

            Click = theme_data.get("click", "")
            Hover = theme_data.get("hover", "")

            # Update the UI elements with the new theme settings
            self.root.configure(background=InterfaceMenu_Background)
            self.new_button.config(background=InterfaceMenu_NewButtonBackground)
            self.open_button.config(background=InterfaceMenu_OpenButtonBackground)

            self.new_image.config(file=NewButton)
            self.open_image.config(file=OpenButton)
            
            for button in self.extra_buttons:
                button.config(fg=InterfaceMenu_ButtonConfigFG, background=InterfaceMenu_Background)

            # Close the settings window
            settings_window.destroy()

        def install_bepinex():
            architecture = get_system_architecture()
            download_url = get_bepinex_download_url(architecture)
            dest = os.path.join(os.getcwd(), "resources/BepInEx.zip")
            if not os.path.isdir(os.path.join(steam_path, foldername, "BepInEx")):
                download_file(download_url, dest)
                extract_zip(dest, os.path.join(steam_path, foldername))
                os.remove(dest)
                doorstop_dest = os.path.join(steam_path, foldername, ".doorstop_version")
                os.remove(doorstop_dest)
                messagebox.showinfo("BepInEx Installed", "BepInEx has been installed, please run the game once and then "
                                                        "exit in order to generate the proper files, then click \"OK\"",
                                    parent=settings_window)
                if not os.path.isdir(os.path.join(steam_path, foldername, "BepInEx", "Plugins")):
                    return "BepInEx not fully installed"
            else:
                messagebox.showinfo("BepInEx Already Installed", f"BepInEx has already been installed to {os.path.join(steam_path, foldername)}")
            if not os.path.isdir(os.path.join(steam_path, foldername, "BepInEx", "Plugins")):
                messagebox.showinfo("BepInEx Partially Installed",
                                    "BepInEx is installed with files missing, please run the game once and then "
                                    "exit in order to generate the proper files, then click \"OK\"",
                                    parent=settings_window)
                if not os.path.isdir(os.path.join(steam_path, foldername, "BepInEx", "Plugins")):
                    return "BepInEx not fully installed"
            settings_window.focus()

        # Done button to save changes and close the window
        buttons = Frame(settings_window, background=PyroPrompt_Background)
        buttons.pack()
        Button(buttons, text="Install BepInEX", bg=PyroPrompt_Background, fg=PyroPrompt_Foreground, command=install_bepinex).grid(row=0, column=1, padx=10, pady=(10, 10))
        Button(buttons, text="Done", bg=PyroPrompt_Background, fg=PyroPrompt_Foreground, command=save_settings).grid(row=1, column=1, padx=10, pady=(10, 10))

    def prompt_for_custom_steam_directory():
        root = Tk()
        root.withdraw()  # Hide the root window
        steam_path = filedialog.askdirectory(initialdir=settings.get("Default Steam Directory", steam_path),title="Select Steam Library Directory")
        if steam_path and os.path.exists(os.path.join(steam_path, "steamapps", "common")):
            return steam_path
        return None

    def find_steam_directory(self, folder_name):
        # First, attempt to get the Steam directory from the registry
        steam_path = get_steam_directory()
        if steam_path and os.path.exists(os.path.join(steam_path, "steamapps", "common", folder_name)):
            return os.path.join(steam_path, "steamapps", "common")

        # Check common custom drive locations
        common_drives = ["C:", "D:", "E:", "F:", "Z:"]
        for drive in common_drives:
            possible_path = os.path.join(drive, "SteamLibrary", "steamapps", "common")
            if os.path.exists(os.path.join(possible_path, folder_name)):
                return possible_path
            program_files_path = os.path.join(drive, "Program Files", "Steam", "steamapps", "common", folder_name)
            if os.path.exists(program_files_path):
                return os.path.join(drive, "Program Files", "Steam", "steamapps", "common")
            
            program_files_x86_path = os.path.join(drive, "Program Files (x86)", "Steam", "steamapps", "common", folder_name)
            if os.path.exists(program_files_x86_path):
                return os.path.join(drive, "Program Files (x86)", "Steam", "steamapps", "common")
                
        # If registry lookup fails, prompt user to select Steam library directory
        steam_path = prompt_for_custom_steam_directory()
        if steam_path and os.path.exists(os.path.join(steam_path, "steamapps", "common", folder_name)):
            return steam_path


        # If still not found, return None
        return None

    def get_steam_directory():
            try:
                # Open the Steam registry key
                reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
                # Query the value of the "InstallPath" entry
                steam_path = winreg.QueryValueEx(reg_key, "InstallPath")[0]
                winreg.CloseKey(reg_key)
                return steam_path
            except FileNotFoundError:
                # If registry lookup fails, return None
                return None

    def _copy_fallback(self, mod, name):
        name = name[0]
        self.new_name = name

    def open_dialog(self, e):
        try:
            mixer.music.load(Click)
            mixer.music.play(loops=0)
        except:
            pass
        messagebox.showwarning("Never Open Mods From Untrusted Sources", "Reminder: Never Open Mods From Untrusted Sources!!")
        current_directory = os.getcwd()
        file = filedialog.askopenfile(title="Select the mod to open", initialdir=current_directory, filetypes=[("Goblin Mod Maker Files", "*.gmm")])
        
        if file is None: return
        
        name = file.name
        file.close()
        
        mod = load(name)
        close(self, False)
        
        name_no_space = mod.mod_name_no_space.get_text()
        csfilepath = os.path.join(current_directory, "projects", name_no_space, "Files", name_no_space + ".cs")
        pyro.CoreUI(lexer=CSharpLexer(), filename=mod.mod_name_no_space.get_text(), filepath=csfilepath, mod=mod, settings=self.settings)

    def enter(self, e):
        # mod_name is the contents of the text box
        mod_name = e.widget.get()
        # no_space is the name of the mod without spaces
        no_space = mod_name.replace(" ", "")
        # First tries to load the mod, if it doesn't exist it creates a new mod
        try:
            mod = load(os.getcwd() + "/projects/" + no_space + "/" + no_space + ".gmm")
        except FileNotFoundError:
            mod = ModObject(no_space)
        # this closes the main menu because we do not need it anymore
        close(self, False)
        # creates a pyro window which will have syntax highlighting for CSharp and will be editing our mod object
        pyro.CoreUI(lexer=CSharpLexer(), filename=no_space, mod=mod, settings=self.settings)


    # This gets called when the "new" button is pressed so it creates a prompt asking for the name of the new mod and
    # calls self.new_fallback when they press "done", None means that if they press "cancel" nothing specific is done
    def new(self, e):
        try:
            mixer.music.load(Click)
            mixer.music.play(loops=0)
        except:
            pass
        create_prompt("New Mod", 
                       ("Mod Name",
                        "Desciption",
                        "Developers (Seperate names by commas)"), 
                        self.new_fallback, 
                        None, 
                        defaults=None
                     )

    # See the new function, this is the function that gets called when the prompt from the new function has "done"
    # clicked
    def new_fallback(self, data, window):
        # first item in the list is the name of the mod
        name = data[0]
    
        if len(name.strip()) > 50:
            return "Mod name is too long"
        
        if not name or name.strip() == "":
            return "Mod name cannot be empty or null"
        
        # check if there is a directory that corresponds to a mod with this name
        # (spaces aren't included in the file names)
        if exists(os.getcwd() + "/projects/" + name.replace(" ", "")):
            # When the fallback to a prompt returns something, the prompt will show that as an error message and
            # keep itself open effectively asking them again
            return "Project Already Exists"
        # make sure the game is set up in a way to support modding
        gameName = self.settings.get("Default Game", "")
        folderName = self.settings.get("Default Game Folder", "")
        steamPath = self.settings.get("Default Steam Directory", "")
        support = verify_game(gameName, gameName if folderName == "" else folderName, steamPath, window)
        if type(support) is str:
            return support
        if not support:
            return ""
        # creates a new mod with this name and information from the prompt
        mod = ModObject(mod_name=name, description=data[1], authors=data[2],  game=gameName, folder_name=folderName,
                        steampath=steamPath)
        # close the menu window because we don't need it anymore
        
        close(self, False)
        name_no_space = mod.mod_name_no_space.get_text()
        current_directory = os.getcwd()
        csfilepath = os.path.join(current_directory, "projects", name_no_space, "Files", name_no_space + ".cs")
        # creates a pyro window which will have syntax highlighting for CSharp and will be editing our mod object
        pyro.CoreUI(lexer=CSharpLexer(), filename=name.replace(" ", ""), filepath=csfilepath, mod=mod, settings=self.settings)


    # This gets called when the "open" button is pressed so it creates a prompt asking for the name of the mod and
    # calls self.load_fallback when they press "done", None means that if they press "cancel" nothing specific is done
    # there is also a warning that will show up in red telling them not to open mods from untrusted sources this is
    # due to the fact that a malicious .gmm file could allow for arbitrary code execution
    def load(self, e):
        create_prompt("Load Mod", ("Mod Name",), self.load_fallback, None,
                    warning="Never Open Mods From Untrusted Sources")
        try:
            mixer.music.load(Click)
            mixer.music.play(loops=0)
        except:
            pass

    # See the load function, this is the function that gets called when the prompt from the load function has "done"
    # clicked
    def load_fallback(self, name):
        # name is a list of values but it is only one long so just replace it with the first item
        name = name[0]
        # If the directory corresponding to the name doesn't exist, they can't open it
        check_path = os.getcwd() + "/projects/" + name.replace(" ", "")
        if not exists(check_path):
            # When the fallback to a prompt returns something, the prompt will show that as an error message and
            # keep itself open effectively asking them again
            return "Project Doesn't Exist"
        try:
            # It attempts to load the .gmm file with the mod name inside of the directory (This should exist assuming
            # the file was generated by this program and they didn't specifically delete it
            mod = load(os.getcwd() + "/projects/" + name.replace(" ", "") + "/" + name.replace(" ", "") + ".gmm")
        except FileNotFoundError:
            # When the fallback to a prompt returns something, the prompt will show that as an error message and
            # keep itself open effectively asking them again
            return "Goblin Mod Maker File Missing"
        # close the main menu because we do not need it anymore
        close(self, False)
        # creates a pyro window which will have syntax highlighting for CSharp and will be editing our mod object
        name_no_space = mod.mod_name_no_space.get_text()
        current_directory = os.getcwd()
        csfilepath = os.path.join(current_directory, "projects", name_no_space, "Files", name_no_space + ".cs")
        pyro.CoreUI(lexer=CSharpLexer(), filename=name.replace(" ", ""), filepath=csfilepath, mod=mod, settings=self.settings)

if __name__ == "__main__":
    # Creates the main menu and then calls the pyro mainloop
    InterfaceMenu()
    # Pyro has a global (static) list in it that all windows add themselves into, each time pyro mainloop happens it
    # updates each of these windows and does all the required tick events, this is to prevent thread conflicts
    pyro.mainloop()
