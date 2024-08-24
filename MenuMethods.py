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

SETTINGS = {}

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
InterfaceMenu_Background = theme_data.get("interfacemenu", {}).get("background", "")
InterfaceMenu_Foreground = theme_data.get("buttonconfig", {}).get("foreground", "")

# This function is used to make the loading screens for Building the mod and for generating the Dotnet files
def create_loading_screen(message="Please Wait..."):
    # Visuals
    root = Tk()
    root.title("Please Wait...")
    root.iconbitmap("resources/isle-goblin-mod-maker.ico")
    root.configure(background=InterfaceMenu_Background)
    # The text it shows it provided via the message parameter
    x = Label(root, text=message, font=("Calibri", 20), background=InterfaceMenu_Background, fg=InterfaceMenu_Foreground)
    x.pack(padx=20, pady=20)
    # This isn't added to the pyro list of windows because it will be deleted before the next visual tick anyway
    # (Visuals freeze during these build methods) - This could be "fixed" by running the build method in a
    # different thread but it isn't necessary to allow them to edit the mod while it is installing
    root.update()
    # it returns x so that you can update the loading text while it is doing one task
    # it returns root so you can destroy it when you are done
    return root, x


# This gets called when the "new" button is pressed so it creates a prompt asking for the name of the new mod and
# calls self.new_fallback when they press "done", None means that if they press "cancel" nothing specific is done
def new(self):
    create_prompt("New Mod", 
                   ("Mod Name",
                    "Desciption"), 
                    partial(new_fallback, self), 
                    None, 
                    defaults=None
                 )
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
    # make sure the game is set up in a way to support modding
    gameName = self.settings.get("Default Game", "")
    folderName = self.settings.get("Default Game Folder", "")
    steamPath = self.settings.get("Default Steam Directory", "")
    support = ModObject.verify_game(gameName, gameName if folderName == "" else folderName, steamPath, window)
    if type(support) is str:
        return support
    if not support:
        return ""
    # creates a new mod with this name and information from the prompt
    mod = ModObject.ModObject(mod_name=name, description=data[1], game=gameName, folder_name=folderName,
                    steampath=steamPath)
    # close the menu window because we don't need it anymore
    # creates a pyro window which will have syntax highlighting for CSharp and will be editing our mod object
    pyro.CoreUI(lexer=CSharpLexer(), filename=name.replace(" ", ""), mod=mod, settings=self.settings)


def _open_fallback(name):
    name = name[0]
    if not exists(os.getcwd() + "/projects/" + name.replace(" ", "")):
        return "Project Doesn't Exist"
    try:
        mod = ModObject.load(os.getcwd() + "/projects/" + name.replace(" ", "") + "/" + name.replace(" ", "") + ".igmm")
    except FileNotFoundError:
        return "Unity Mod Maker File Missing"
    global SETTINGS
    pyro.CoreUI(lexer=CSharpLexer(), filename=name.replace(" ", ""), mod=mod, settings=SETTINGS)


def open(settings):
    global SETTINGS
    SETTINGS = settings
    create_prompt("Load Mod", ("Mod Name",), _open_fallback, None, warning="Never Open Mods From Untrusted Sources")


# This gets called when they press the save button on the menubar (and later when they do ctrl+s)
def save(window, filename):
    # directory this programming is running in
    current_directory = os.getcwd()
    # this is the directory for the mod
    folder_path = os.path.join(current_directory, "projects/" + filename)
    try:
        # try to make the project folder because it might not exist
        os.mkdir(os.path.join(current_directory, "projects"))
    except FileExistsError:
        # it already exists so it is fine, you can continue
        pass
    try:
        # try to make the mod directory (it's in the project folder which is why we needed to make sure that existed)
        os.mkdir(folder_path)
    except FileExistsError:
        # it already exists so we are good
        pass
    # calls the save method on the mod object now that we made sure all the correct folders existed
    ModObject.save(window.mod, location=folder_path + "/" + filename + ".igmm")


def _copy_fallback(window, name):
    name = name[0]
    return ModObject.copy(window.mod, name)


def copy(window):
    create_prompt("Copy Mod", ("New Mod Name",), partial(_copy_fallback, window), None)

def openSearch(window):
    create_prompt("Search", ("Search For",), partial(searchFallback, window), None)

def searchFallback(window, text):
    window.search(regexp=text[0])

def openGTL(window):
    create_int_prompt("Go To Line", ("Enter Line Number"), partial(gTLFallback, window), None, min_value=1)

def gTLFallback(window, num):
    window.gotoline(line_number=num)


def build_install(window):
    root, text = create_loading_screen()

    def set_text(x):
        text.configure(text=x)
        root.update()

    if window.mod.install(destroyonerror=root, progress_updater=set_text):
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
    with builtins.open(f"{folder_path}/{name_no_space}.cs", "w") as f:
        code = "\n".join([s for s in window.mod.code.get_text().splitlines() if s])
        f.write(code)
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
    # def create_harmony_patch(self, in_class, method, prefix=True, parameters=list(), have_instance=True, result=None):
    scroll_data = window.text.yview()
    ChangeManager.log_action(window.mod, True)
    window.mod.create_harmony_patch(values[1], values[0], prefix=values[3] == "Prefix", parameters=values[2].split(","),
                                    have_instance=values[5] != "False",
                                    result=values[4] if values[4] != "None" else None)
    window.refresh(False)
    window.text.yview_moveto(scroll_data[0])


def create_harmony_patch(window):
    create_prompt("Create Harmony Patch", ("Function Name", "Function's Class", "Parameters (separate by comma)", "Prefix/Postfix", "Return Type", "Have Instance?"),
                  partial(_harmony_patch_fallback, window), None,
                  defaults={"Prefix/Postfix": "Prefix", "Return Type": "None", "Have Instance?": "False"})


def _config_item_fallback(window, values):
    scroll_data = window.text.yview()
    ChangeManager.log_action(window.mod, True)
    window.mod.add_config(values[0], values[1], values[2], values[3], values[4])
    window.refresh(False)
    window.text.yview_moveto(scroll_data[0])


def create_config_item(window):
    create_prompt("Create Config Item", ("Variable Name", "Data Type (e.g. int)", "Default Value (C# formatting)",
                                         "Definition (Name in List)", "Description (Info When Hovered Over)"),
                  partial(_config_item_fallback, window), None)


def _keybind_fallback(window, values):
    scroll_data = window.text.yview()
    ChangeManager.log_action(window.mod, True)
    window.mod.add_config(values[0], "BepInEx.Configuration.KeyboardShortcut",
                          "new BepInEx.Configuration.KeyboardShortcut(UnityEngine.KeyCode." + values[1] + ")",
                          values[2], values[3])
    window.mod.declare_variable("bool", values[0] + "JustPressed", "false")
    window.mod.declare_variable("bool", values[0] + "Down", "false")
    window.mod.update.contents.insert_block_after(CodeBlock([
        CodeLine(values[0] + "JustPressed = " + values[0] + ".Value.IsDown();"),
        CodeLine("if (" + values[0] + ".Value.IsDown()){"),
        CodeLine(values[0] + "Down = true;").indent(),
        CodeLine("if(mEnabled.Value){").indent(),
        CodeLine("// Code For When Key is Pressed").indent().indent(),
        ModObject.end_block().indent(),
        ModObject.end_block(),
        CodeLine("if (" + values[0] + ".Value.IsUp()){"),
        CodeLine(values[0] + "Down = false;").indent(),
        CodeLine("if(mEnabled.Value){").indent(),
        CodeLine("// Code For When Key is Released").indent().indent(),
        ModObject.end_block().indent(),
        ModObject.end_block()
    ]).indent().indent().indent())
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
    labels[1].config(fg="#347deb")
