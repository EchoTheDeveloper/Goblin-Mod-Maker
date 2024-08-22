"""
This module is the main module of the entire program, running this file is how you start the application
It contains the code for the main menu which is what you are greeted with when you are using the program
"""

import os
from tkinter import messagebox, filedialog
from tkinter import *
from tkinter import ttk
from PIL import ImageTk, Image
from functools import partial
from winsound import *
from pygame import mixer
import json

from pygments.lexers.dotnet import CSharpLexer
import pyroprompt

# Makes it easier to make a prompt
create_prompt = pyroprompt.create_prompt
from os.path import exists
from ModObject import *
import pyro

# keep track of the number of windows so you only open the main menu when the last one is closed
window_count = 0
# keep track of whether it should even open the main menu depending on if there is one already open (avoid more than one
# menu open at a time
can_make_menu = True

DEFAULT_SETTINGS = {
    "Default Game": "Isle Goblin",
    "Default Game Folder": "Isle Goblin Playtest",
    "Default Steam Directory": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\",
    "Show Line Numbers": True

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
theme_data = load_theme('resources/themes/' + settings.get("Selected Theme", "Default") + ".json")

InterfaceMenu_Background = theme_data.get("interfacemenu_background", "")
InterfaceMenu_Geometry = theme_data.get("interfaceMenu_geometry", "")
InterfaceMenu_NewButtonBackground = theme_data.get("interfacemenu_newbuttonbackground", "")
InterfaceMenu_OpenButtonBackground = theme_data.get("interfacemenu_openbuttonbackground", "")
InterfaceMenu_MouseEnter = theme_data.get("interfacemenu_mouseenter", "")
InterfaceMenu_MouseExit = theme_data.get("interfacemenu_mouseexit", "")
InterfaceMenu_ButtonConfigFG = theme_data.get("interfacemenu_buttonconfig_foreground", "")
InterfaceMenu_ButtonConfigBG = theme_data.get("interfacemenu_buttonconfig_background", "")

PyroPrompt_Background = theme_data.get("pyroprompt_background", "")
PyroPrompt_Foreground = theme_data.get("pyroprompt_foreground", "")
PyroPrompt_WarningTextColor = theme_data.get("pyroprompt_warningtextcolor", "")

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
        self.root = Tk()
        mixer.init()
        self.root.configure(background=InterfaceMenu_Background)
        self.root.geometry(InterfaceMenu_Geometry)
        self.root.resizable(0, 0)
        self.root.title("Isle Goblin Mod Maker - Main Menu")
        self.root.iconbitmap("resources/isle-goblin-mod-maker.ico")
        self.new_image = PhotoImage(file=NewButton)
        self.open_image = PhotoImage(file=OpenButton)
        self.new_button = Label(self.root, image=self.new_image, background=InterfaceMenu_NewButtonBackground)
        self.open_button = Label(self.root, image=self.open_image, background=InterfaceMenu_OpenButtonBackground)
        self.new_button.place(x=20, y=20)
        self.open_button.place(x=240, y=20)
        # The buttons are bound to the self.new function and self.load function because they are new and load buttons
        self.new_button.bind("<Button-1>", self.new)
        self.open_button.bind("<Button-1>", self.load)

        def mouse_enter(e):
            e.widget.config(borderwidth=5, fg=InterfaceMenu_MouseEnter)
            try:
                mixer.music.load(Hover)
                mixer.music.play(loops=0)
            except:
                pass

        def mouse_exit(e):
            e.widget.config(borderwidth=0, fg=InterfaceMenu_MouseExit)

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

        self.extra_buttons = []

        self.open_external = Label(self.root, text="Open From Isle Goblin Mod Maker (.igmm) File")
        self.open_external.place(x=20, y=150)
        self.open_external.bind("<Button-1>", self.open_dialog)
        self.extra_buttons.append(self.open_external)

        self.settings_button = Label(self.root, text="Open IGMM Settings")
        self.settings_button.place(x=20, y=180)
        self.settings_button.bind("<Button-1>", self.open_settings_window)
        self.extra_buttons.append(self.settings_button)

        for button in self.extra_buttons:
            button.config(font=("Calibri", 15), fg=InterfaceMenu_ButtonConfigFG, background=InterfaceMenu_Background)
            button.bind("<Enter>", mouse_enter)
            button.bind("<Leave>", mouse_exit)

        self.new_button.bind("<Enter>", new_button_hover_enter)
        self.new_button.bind("<Leave>", new_button_hover_exit)
        self.open_button.bind("<Enter>", open_button_hover_enter)
        self.open_button.bind("<Leave>", open_button_hover_exit)

        # Instead of doing root.mainloop we do pyro.add_window to avoid thread conflicts, pyro deals with calling
        # root.update() on  everything in the pyro window list, there is also no need to remove closed windows from this
        pyro.add_window(self.root)

    def find_settings(self):
        settings = None
        try:
            with open('settings.json') as json_file:
                settings = json.load(json_file)
                for item in DEFAULT_SETTINGS:
                    if item not in settings:
                        settings[item] = DEFAULT_SETTINGS[item]
            with open('settings.json', 'w') as json_file:
                json.dump(settings, json_file)
        except Exception:
            with open('settings.json', 'w') as json_file:
                json.dump(DEFAULT_SETTINGS, json_file)
                settings = DEFAULT_SETTINGS
        return settings
    
    def open_settings_window(self, event=None):
        try:
            mixer.music.load(Click)
            mixer.music.play(loops=0)
        except:
            pass
        title = "Isle Goblin Mod Maker Settings"
        settings_window = Toplevel(self.root)
        settings_window.title(title)
        Frame(settings_window, width=500, background=PyroPrompt_Background).pack()
        frame = Frame(settings_window, width=500, background=PyroPrompt_Background)
        frame.pack(fill="x")
        heading = Label(frame, text=title, font=("Calibri", 18), background=PyroPrompt_Background, fg=PyroPrompt_Foreground)
        heading.pack(fill="x", pady=10)
        settings_window.configure(background=PyroPrompt_Background)
        settings_window.resizable(0, 0)
        settings_window.iconbitmap("resources/isle-goblin-mod-maker.ico")

        # Create and pack widgets with default values loaded from settings
        Label(settings_window, background=PyroPrompt_Background, fg=PyroPrompt_Foreground, font=("Calibri", 12), text="Default Game Folder").pack(fill="x", padx=10)
        game_folder_entry = Entry(settings_window, background=PyroPrompt_Background, fg=PyroPrompt_Foreground, font=("Calibri", 12))
        game_folder_entry.insert(0, self.settings.get("Default Game Folder", ""))
        game_folder_entry.pack(fill="x", padx=10, pady=10)

        Label(settings_window, background=PyroPrompt_Background, fg=PyroPrompt_Foreground, font=("Calibri", 12), text="Default Steam Directory").pack(fill="x", padx=10)
        steam_dir_entry = Entry(settings_window, background=PyroPrompt_Background, fg=PyroPrompt_Foreground, font=("Calibri", 12))
        steam_dir_entry.insert(0, self.settings.get("Default Steam Directory", ""))
        steam_dir_entry.pack(fill="x", padx=10, pady=10)

        theme_folder = "resources/themes"
        themes = [os.path.splitext(file)[0] for file in os.listdir(theme_folder) if file.endswith(".json")]

        # Default selection for the dropdown
        clicked = StringVar()
        clicked.set(self.settings.get("Selected Theme", "Default"))  # Set the last selected theme or to Default

        Label(settings_window, background=PyroPrompt_Background, fg=PyroPrompt_Foreground, font=("Calibri", 12), text="Select Theme").pack(fill="x", padx=10)
        themeDrop = OptionMenu(settings_window, clicked, *themes)
        themeDrop.config(bg=PyroPrompt_Background, fg=PyroPrompt_Foreground)
        themeDrop["menu"].config(bg=PyroPrompt_Background, fg=PyroPrompt_Foreground)
        themeDrop.pack(fill="x", padx=10, pady=10)

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
            
            # Save the settings to the JSON file
            with open('settings.json', 'w') as json_file:
                json.dump(self.settings, json_file, indent=4)
            
            # Reload the theme
            theme_data = load_theme('resources/themes/' + self.settings.get("Selected Theme", "Default") + ".json")
            
            # Update the theme settings
            global InterfaceMenu_Background, InterfaceMenu_Geometry, InterfaceMenu_NewButtonBackground, InterfaceMenu_OpenButtonBackground
            global InterfaceMenu_MouseEnter, InterfaceMenu_MouseExit, InterfaceMenu_ButtonConfigFG, InterfaceMenu_ButtonConfigBG
            global PyroPrompt_Background, PyroPrompt_Foreground, PyroPrompt_WarningTextColor
            global NewButton, OpenButton
            global Click, Hover
            
            InterfaceMenu_Background = theme_data.get("interfacemenu_background", "")
            InterfaceMenu_Geometry = theme_data.get("interfaceMenu_geometry", "")
            InterfaceMenu_NewButtonBackground = theme_data.get("interfacemenu_newbuttonbackground", "")
            InterfaceMenu_OpenButtonBackground = theme_data.get("interfacemenu_openbuttonbackground", "")
            InterfaceMenu_MouseEnter = theme_data.get("interfacemenu_mouseenter", "")
            InterfaceMenu_MouseExit = theme_data.get("interfacemenu_mouseexit", "")
            InterfaceMenu_ButtonConfigFG = theme_data.get("interfacemenu_buttonconfig_foreground", "")
            InterfaceMenu_ButtonConfigBG = theme_data.get("interfacemenu_buttonconfig_background", "")
            
            PyroPrompt_Background = theme_data.get("pyroprompt_background", "")
            PyroPrompt_Foreground = theme_data.get("pyroprompt_foreground", "")
            PyroPrompt_WarningTextColor = theme_data.get("pyroprompt_warningtextcolor", "")

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

        # Done button to save changes and close the window
        buttons = Frame(settings_window, background=PyroPrompt_Background)
        buttons.pack()
        Button(buttons, text="Done", bg=PyroPrompt_Background, fg=PyroPrompt_Foreground, command=save_settings).grid(row=0, column=1, padx=10, pady=(10, 10))


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
        file = filedialog.askopenfile(filetypes=[("Isle Goblin Mod Maker Files", "*.igmm")])
        if file is None: return
        name = file.name
        file.close()
        mod = load(name)
        create_prompt("Create Mod From .igmm file", ("New Mod Name",), partial(self._copy_fallback, mod), None)
        #pyro.CoreUI(lexer=CSharpLexer(), filename=mod.mod_name_no_space.get_text(), mod=mod)

    def enter(self, e):
        # mod_name is the contents of the text box
        mod_name = e.widget.get()
        # no_space is the name of the mod without spaces
        no_space = mod_name.replace(" ", "")
        # First tries to load the mod, if it doesn't exist it creates a new mod
        try:
            mod = load(os.getcwd() + "/projects/" + no_space + "/" + no_space + ".igmm")
        except FileNotFoundError:
            mod = ModObject(no_space)
        # this closes the main menu because we do not need it anymore
        close(self, False)
        # creates a pyro window which will have syntax highlighting for CSharp and will be editing our mod object
        pyro.CoreUI(lexer=CSharpLexer(), filename=no_space, mod=mod, settings=self.settings)


    # This gets called when the "new" button is pressed so it creates a prompt asking for the name of the new mod and
    # calls self.new_fallback when they press "done", None means that if they press "cancel" nothing specific is done
    def new(self, e):
        create_prompt("New Mod", ("Mod Name",
                                  "Desciption",
                                  "Game Name (Check Spelling and Punctuation)",
                                  "Name of Folder in Steam Files (If different from Game Name)",
                                  "PolyTech (Poly Bridge Modding Framework)",
                                  "Steam Directory"), self.new_fallback, None, defaults={
            "Game Name (Check Spelling and Punctuation)": self.settings["Default Game"],
            "Name of Folder in Steam Files (If different from Game Name)": self.settings["Default Game Folder"],
            "PolyTech (Poly Bridge Modding Framework)": "Auto",
            "Steam Directory": self.settings["Default Steam Directory"]
        })
        try:
            mixer.music.load(Click)
            mixer.music.play(loops=0)
        except:
            pass

    # See the new function, this is the function that gets called when the prompt from the new function has "done"
    # clicked
    def new_fallback(self, data, window):
        # first item in the list is the name of the mod
        name = data[0]

        if not name or name.strip() == "":
            return "Mod name cannot be empty or null"
        # check if there is a directory that corresponds to a mod with this name
        # (spaces aren't included in the file names)
        if exists(os.getcwd() + "/projects/" + name.replace(" ", "")):
            # When the fallback to a prompt returns something, the prompt will show that as an error message and
            # keep itself open effectively asking them again
            return "Project Already Exists"
        # Decide whether the mod should use polytech
        poly_tech = data[4]
        if poly_tech.lower() == "true":
            poly_tech = True
        elif poly_tech.lower() == "false":
            poly_tech = False
        else:
            poly_tech = data[1] == "Poly Bridge 2"
        # make sure the game is set up in a way to support modding
        support = verify_game(data[2], data[2] if data[3] == "" else data[3], data[5], window)
        if type(support) is str:
            return support
        if not support:
            return ""
        # creates a new mod with this name and information from the prompt
        mod = ModObject(name, description=data[1], poly_tech=poly_tech, game=data[2], folder_name=None if data[3] == "" else data[3],
                        steampath=data[5])
        # close the menu window because we don't need it anymore
        close(self, False)
        # creates a pyro window which will have syntax highlighting for CSharp and will be editing our mod object
        pyro.CoreUI(lexer=CSharpLexer(), filename=name.replace(" ", ""), mod=mod, settings=self.settings)


    # This gets called when the "open" button is pressed so it creates a prompt asking for the name of the mod and
    # calls self.load_fallback when they press "done", None means that if they press "cancel" nothing specific is done
    # there is also a warning that will show up in red telling them not to open mods from untrusted sources this is
    # due to the fact that a malicious .igmm file could allow for arbitrary code execution
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
            # It attempts to load the .igmm file with the mod name inside of the directory (This should exist assuming
            # the file was generated by this program and they didn't specifically delete it
            mod = load(os.getcwd() + "/projects/" + name.replace(" ", "") + "/" + name.replace(" ", "") + ".igmm")
        except FileNotFoundError:
            # When the fallback to a prompt returns something, the prompt will show that as an error message and
            # keep itself open effectively asking them again
            return "Isle Goblin Mod Maker File Missing"
        # close the main menu because we do not need it anymore
        close(self, False)
        # creates a pyro window which will have syntax highlighting for CSharp and will be editing our mod object
        pyro.CoreUI(lexer=CSharpLexer(), filename=name.replace(" ", ""), mod=mod, settings=self.settings)

if __name__ == "__main__":
    # Creates the main menu and then calls the pyro mainloop
    InterfaceMenu()
    # Pyro has a global (static) list in it that all windows add themselves into, each time pyro mainloop happens it
    # updates each of these windows and does all the required tick events, this is to prevent thread conflicts
    pyro.mainloop()
