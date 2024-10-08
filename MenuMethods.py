from tkinter import messagebox

from pyroprompt import *
import pyro
from os.path import exists
import os
from ModObject import ModObject
import ModObject
from tkinter import *
import ChangeManager
from pygments.lexers.dotnet import CSharpLexer
from CodeManager import *
import builtins  
from ModObjectBuilder import *


SETTINGS = {}

def load_theme(filename):
    with builtins.open(filename, 'r') as file:
        data = json.load(file)
    return data

def load_settings():
    with builtins.open("settings.json", 'r') as file:
        data = json.load(file)
    return data

def refresh_theme(root=None):
    global theme_data, InterfaceMenu_Background, InterfaceMenu_Foreground, PyroPrompt_LinkText

    # Reload the theme data
    settings = load_settings()
    theme_data = load_theme('resources/themes/' + settings.get("Selected Theme", "Isle Goblin") + ".json")

    # Update global theme variables
    InterfaceMenu_Background = theme_data.get("interfacemenu", {}).get("background", "")
    InterfaceMenu_Foreground = theme_data.get("buttonconfig", {}).get("foreground", "")
    PyroPrompt_LinkText = theme_data.get("pyroprompt", {}).get("linktextcolor", "")

    if root:
        root.configure(background=InterfaceMenu_Background)
        for widget in root.winfo_children():
            if isinstance(widget, Label):
                widget.configure(background=InterfaceMenu_Background, fg=InterfaceMenu_Foreground)
    else:
        # Update the UI elements that rely on these variables
        # Example: Updating the background and foreground colors
        for window in pyro.get_windows():  # Assuming pyro has a method to get active windows
            window.configure(background=InterfaceMenu_Background)
            for widget in window.winfo_children():
                if isinstance(widget, Label):
                    widget.configure(background=InterfaceMenu_Background, fg=InterfaceMenu_Foreground)



def create_loading_screen(message="Please Wait..."):
    # Visuals
    root = Tk()
    root.title("Please Wait...")
    refresh_theme(root)  # Pass root to refresh_theme
    root.iconbitmap("resources/goblin-mod-maker.ico")
    root.configure(background=InterfaceMenu_Background)

    # The text it shows is provided via the message parameter
    x = Label(root, text=message, font=("Calibri", 20), background=InterfaceMenu_Background, fg=InterfaceMenu_Foreground)
    x.pack(padx=20, pady=20)

    root.update()
    return root, x


# This gets called when the "new" button is pressed so it creates a prompt asking for the name of the new mod and
# calls self.new_fallback when they press "done", None means that if they press "cancel" nothing specific is done
def new(self, e=None):
    create_prompt("New Mod", 
                   ("Mod Name",
                    "Description",
                    "Developers (Separate names by commas)"), 
                    partial(new_fallback, self),
                    None, 
                    defaults=None
                 )
    try:
        mixer.music.load(Click)
        mixer.music.play(loops=0)
    except:
        pass

#KEEP GETTING PROBLEMS WITH STYLING WHEN CREATING OR OPENING A MOD
# See the new function, this is the function that gets called when the prompt from the new function has "done"
# clicked
def new_fallback(self, data):
    # First item in the list is the name of the mod
    name = data[0].strip()

    if len(name) > 50:
        return "Mod name is too long"

    if not name:
        return "Mod name cannot be empty or null"

    # Check if a directory already exists for this mod
    mod_directory = os.path.join(os.getcwd(), "projects", name.replace(" ", ""))
    if exists(mod_directory):
        return "Project Already Exists"
    
    # Ensure the game is set up to support modding
    gameName = self.settings.get("Default Game", "")
    folderName = self.settings.get("Default Game Folder", "")
    steamPath = self.settings.get("Default Steam Directory", "")
    support = ModObject.verify_game(gameName, gameName if folderName == "" else folderName, steamPath, self)
    if isinstance(support, str):
        return support
    if not support:
        return ""

    # Create a new mod object
    mod = ModObject.ModObject(mod_name=name, description=data[1], authors=data[2], game=gameName, folder_name=folderName, steampath=steamPath)
    
    # Prepare the C# file path
    name_no_space = mod.mod_name_no_space.get_text()
    csfilepath = os.path.join(mod_directory, "Files", f"{name_no_space}.cs")

    # Create a new Pyro window with syntax highlighting
    new_editor = pyro.CoreUI(lexer=CSharpLexer(), filename=name, filepath=csfilepath, mod=mod, settings=self.settings)
    new_editor.uiconfig()  # Ensure the UI configuration is applied

def new_file(self, e=None):
    create_prompt("New File", 
                ("File Name (if no extention added, .cs will be added)",), 
                    partial(new_file_fallback, self), 
                    None, 
                    defaults=None
                )

def new_file_fallback(self, data):
    filename = data[0]
    
    # Replace spaces with underscores for the filename
    name_no_space = ''.join([word.capitalize() for word in filename.split(" ")])
    
    mod_name_no_space = self.mod.mod_name_no_space.get_text()
    
    current_directory = os.getcwd()
    
    # Add .cs if no extension is provided
    if not os.path.splitext(name_no_space)[1]:
        name_no_space += ".cs"
    
    filepath = os.path.join(current_directory, "projects", mod_name_no_space, "Files", name_no_space)
    
    # Capitalize letters for the class name (remove spaces and capitalize each word)
    class_name = ''.join([word.capitalize() for word in os.path.splitext(filename)[0].split()])
    
    file_content = f"""using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace {mod_name_no_space}
{{
    public class {class_name}
    {{
        // Add Code
    }}
}}
"""

    try:
        # Create the new file and write the content
        with builtins.open(filepath, "x") as f:
            f.write(file_content)
    except FileExistsError:
        return "File already exists."
    except Exception as e:
        messagebox.showerror("Error", str(e))

    self.loadfile(filepath)
    self.file_treeview.adjust_column_width()

    
def _open_fallback(name):
    name = name[0]
    if not exists(os.getcwd() + "/projects/" + name.replace(" ", "")):
        return "Project Doesn't Exist"
    try:
        mod = ModObject.load(os.getcwd() + "/projects/" + name.replace(" ", "") + "/" + name.replace(" ", "") + ".gmm")
    except FileNotFoundError:
        return "Unity Mod Maker File Missing"
    global SETTINGS
    pyro.CoreUI(lexer=CSharpLexer(), filename=name.replace(" ", ""), mod=mod, settings=SETTINGS)

def open(settings, e=None):
    global SETTINGS
    SETTINGS = settings
    create_prompt("Load Mod", ("Mod Name",), _open_fallback, None, warning="Never Open Mods From Untrusted Sources")

# This gets called when they press the save button on the menubar (and later when they do ctrl+s)
def save(window, filename, e=None):
    # directory this program is running in
    current_directory = os.getcwd()
    
    # check if filename is an absolute path
    if not os.path.isabs(filename):
        # this is the directory for the mod
        folder_path = os.path.join(current_directory, "projects", filename)
    else:
        folder_path = filename
    
    try:
        # try to make the project folder because it might not exist
        os.mkdir(os.path.join(current_directory, "projects"))
    except FileExistsError:
        # it already exists so it is fine, you can continue
        pass

    try:
        # try to make the mod directory (inside the project folder)
        os.mkdir(folder_path)
    except FileExistsError:
        # it already exists so we are good
        pass
    
    # calls the save method on the mod object now that we made sure all the correct folders existed
    ModObject.save(window.mod, location=os.path.join(folder_path, filename + ".gmm"))

def _copy_fallback(window, name):
    name = name[0]
    return ModObject.copy(window.mod, name)

def copy(window):
    create_prompt("Copy Mod", ("New Mod Name",), partial(_copy_fallback, window), None)


def openSearch(window, e=None):
    create_prompt("Search", ("Search For",), partial(searchFallback, window), None)

def searchFallback(window, text):
    window.search(regexp=text[0])


def openGTL(window, e=None):
    create_int_prompt("Go To Line", ("Enter Line Number"), partial(gTLFallback, window), None, min_value=1)

def gTLFallback(window, num):
    window.go_to_line(line_number=num)


def build_install(window, e=None):
    root, text = create_loading_screen()

    def set_text(x):
        text.configure(text=x)
        root.update()

    if window.mod.install(window=window, destroyonerror=root, progress_updater=set_text):
        root.destroy()
        messagebox.showinfo("Success", "Mod Successfully Installed")
        
        mod_folder_name = f"{window.mod.mod_name.get_text()}_{window.mod.version.get_text()}"
        install_path = os.path.join(window.mod.steampath, window.mod.folder_name, "BepInEx/plugins")
        mod_install_path = os.path.join(install_path + "/" + mod_folder_name)
        
        os.startfile(mod_install_path)


def export_cs(window):
    root = create_loading_screen("Generating C# File...")[0]
    name_no_space = window.mod.mod_name_no_space.get_text()
    current_directory = os.getcwd()
    folder_path = os.path.join(current_directory, "projects/" + name_no_space)
    try:
        os.mkdir(os.path.join(current_directory, "projects"))
    except FileExistsError:
        pass
    try:
        os.mkdir(folder_path)
    except FileExistsError:
        pass
    try:
        with builtins.open(f"{folder_path}/{name_no_space}.cs", "w") as f:
            # code = "\n".join([s for s in  if s])
            f.write(window.text.get()) # doesnt work
    except:
        messagebox.showerror("Error", "Unable to get code from script")
    root.destroy()
    messagebox.showinfo("Success", "File Created Successfully")
    return root


def export_dotnet(window, independent=True):
    root = create_loading_screen("Generating Dotnet Files...")[0]
    if ModObject.create_files(window.mod, destroyonerror=root) is not None:
        if independent:
            root.destroy()
            messagebox.showinfo("Success", "Files Created Successfully")
        return root


def _change_name_fallback(window, name):
    ChangeManager.log_action(window.mod, True)
    window.mod.set_mod_name(name[0])
    window.refresh(False)

def change_mod_name(window):
    create_prompt("Rename Mod", ("New Name",), partial(_change_name_fallback, window), None, {"New Name": window.mod.mod_name.get_text()})


def _change_version_fallback(window, name):
    ChangeManager.log_action(window.mod, True)
    window.mod.set_version(name[0])
    window.refresh(False)

def change_mod_version(window):
    create_prompt("Change Mod Version", ("New Version",), partial(_change_version_fallback, window), None, {"New Version": window.mod.version.get_text()})


def _change_authors_fallback(window, name):
    ChangeManager.log_action(window.mod, True)
    window.mod.set_authors(name[0])

def change_mod_authors(window):
    create_prompt("Change Developers", ("Developer Names (Seperate Names by comma)",), partial(_change_authors_fallback, window), None, {"Developer Names (Seperate Names by comma)": window.mod.authors})


def _harmony_patch_fallback(window, values):
    # Save scroll position
    scroll_data = window.text.yview()

    # Log action for undo/redo purposes
    ChangeManager.log_action(window.mod, True)

    # Generate the Harmony patch code
    patch_code = window.mod.create_harmony_patch(
        values[1], values[0],
        prefix=values[3] == "Prefix",
        parameters=values[2].split(","),
        have_instance=values[5] != "False",
        result=values[4] if values[4] != "None" else None
    )

    # Get current text content
    current_text = window.text.get("1.0", "end-1c")

    # Find the position of the last closing brace `}` of the class (excluding any at the very end of the file)
    class_end_position = current_text.rfind("}", 0, current_text.rfind("}") - 1)

    # Find the class indentation level
    class_start_position = current_text.rfind("class ", 0, class_end_position)
    class_lines = current_text[class_start_position:class_end_position].splitlines()
    
    class_indentation = ''
    for line in class_lines:
        stripped_line = line.strip()
        if stripped_line.startswith("class "):
            class_indentation = line[:line.index("class ")]
            break

    # Format the patch code with correct indentation
    patch_lines = patch_code.splitlines()
    indented_patch_code = [class_indentation + patch_lines[0]]  # First line with class indentation
    indented_patch_code += [class_indentation + "        " + line for line in patch_lines[1:]]  # Indent the rest

    # Convert to a single string
    indented_patch_code_str = "\n".join(indented_patch_code)

    # Insert the patch code right before the closing brace of the class
    if class_end_position != -1:
        updated_text = (
            current_text[:class_end_position].rstrip() + 
            "\n" + indented_patch_code_str + 
            "\n    " + current_text[class_end_position:]  # Retain the original closing brace
        )

        window.text.delete("1.0", "end")
        window.text.insert("1.0", updated_text)

    # Refresh and restore scroll position
    window.refresh(False)
    window.text.yview_moveto(scroll_data[0])

def create_harmony_patch(window):
    create_prompt("Create Harmony Patch", ("Function Name", "Function's Class", "Parameters (separate by comma)", "Prefix/Postfix", "Return Type", "Have Instance?"),
                  partial(_harmony_patch_fallback, window), None,
                  defaults={"Prefix/Postfix": "Prefix", "Return Type": "None", "Have Instance?": "False"})


def _config_item_fallback(window, values):
    # Save scroll position
    scroll_data = window.text.yview()

    # Log action for undo/redo purposes
    ChangeManager.log_action(window.mod, True)

    # Get the config strings (without native mode)
    config_entry_declaration, config_definition, constructor_content = window.mod.add_config(
        values[0], values[1], values[2], values[3], values[4], native=False
    )

    # Find the first occurrence of "ConfigEntry" and add the config entry declaration below it
    config_entry_index = window.text.search("ConfigEntry", "1.0", stopindex="end")
    if config_entry_index:
        # Insert config entry declaration after the found line
        window.text.insert(f"{config_entry_index} lineend +1c", config_entry_declaration + "\n")

    # Find the first occurrence of "ConfigDescription" and add the config definition below it
    config_definition_index = window.text.search("ConfigDefinition", "1.0", stopindex="end")
    if config_definition_index:
        # Insert config definition after the found line
        window.text.insert(f"{config_definition_index} lineend +1c", config_definition + "\n")

    # Find the first occurrence of "public {mod_name_no_space}" (constructor) and insert constructor content after its opening curly bracket
    method_index = window.text.search("ConfigDescription", "1.0", stopindex="end")
    if method_index:
        # Search for the opening curly bracket '{' after the method declaration
        method_body_index = window.text.search("{", method_index, stopindex="end")
        if method_body_index:
            # Insert constructor content after the opening curly bracket
            window.text.insert(f"{method_body_index} +1c", "\n" + constructor_content)

    # Refresh and restore scroll position
    window.refresh(False)
    window.text.yview_moveto(scroll_data[0])

def create_config_item(window):
    create_prompt("Create Config Item", ("Variable Name", "Data Type (e.g. int)", "Default Value (C# formatting)",
                                         "Definition (Name in List)", "Description (Info When Hovered Over)"),
                  partial(_config_item_fallback, window), None)


def _keybind_fallback(window, values):
    scroll_data = window.text.yview()
    ChangeManager.log_action(window.mod, True)

    # Add configuration for the keybind
    _config_item_fallback(window, [
        values[0],  # Config key
        "BepInEx.Configuration.KeyboardShortcut",  # Config type
        f"new BepInEx.Configuration.KeyboardShortcut(UnityEngine.KeyCode.{values[1]})",  # Config value
        values[2],  # Config description
        values[3]   # Default value
    ])

    # Declare variables for key states
    window.mod.declare_variable("bool", f"{values[0]}JustPressed", "false")
    window.mod.declare_variable("bool", f"{values[0]}Down", "false")

    # Find the update method with Allman style and insert keybind logic
    update_method_index = window.text.search("void Update()", "1.0", stopindex="end")
    if update_method_index:
        method_body_index = window.text.search("{", update_method_index, stopindex="end")
        if method_body_index:
            keybind_logic = f"""
            // Keybind logic for {values[0]}
            {values[0]}JustPressed = {values[0]}.Value.IsDown();
            if ({values[0]}.Value.IsDown())
            {{
                {values[0]}Down = true;
                if (mEnabled.Value)
                {{
                    // Code For When Key is Pressed
                }}
            }}
            if ({values[0]}.Value.IsUp())
            {{
                {values[0]}Down = false;
                if (mEnabled.Value)
                {{
                    // Code For When Key is Released
                }}
            }}"""
            # Insert the keybind logic inside the Update method
            window.text.insert(f"{method_body_index} +1c", keybind_logic)

    window.refresh(False)
    window.text.yview_moveto(scroll_data[0])


def keycode_link(e):
    try:
        import webbrowser
        webbrowser.open_new("https://docs.unity3d.com/ScriptReference/KeyCode.html")
    except ImportError:
        messagebox.create_error("Missing Module",
                                "Missing the \"webbrowser\" module")

def create_keybind(window):
    labels = create_prompt("Create Keybind", ("Variable Name", "Default Keycode (Click For List)",
                                              "Definition (Name in Settings)", "Description (Info When Hovered Over)"),
                           partial(_keybind_fallback, window), None,
                           defaults={"Default Keycode (Click For List)": "None"})
    labels[1].bind("<Button-1>", keycode_link)
    refresh_theme()
    labels[1].config(fg=PyroPrompt_LinkText)

def _npc_fallback(window, values):
    print("fallback")
def create_npc_data_asset(window):
    create_prompt("Create Config Item", ("Variable Name", "Data Type (e.g. int)", "Default Value (C# formatting)",
                                         "Definition (Name in List)", "Description (Info When Hovered Over)"),
                partial(_npc_fallback, window), None)