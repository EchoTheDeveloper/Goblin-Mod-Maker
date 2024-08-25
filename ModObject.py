import shutil
from tkinter import messagebox, filedialog

from ModObjectBuilder import *
from CodeManager import *
import pickle
import os
import subprocess
from tkinter import *
import json
import requests
import zipfile
import platform
from datetime import datetime
import winreg

VERSION = "1.3.0"
windows = []


def get_windows(): return windows
import pyroprompt
create_prompt = pyroprompt.create_prompt

class LimitedModObject:
    def __init__(self):
        pass
    
def load_settings():
    with open("settings.json", 'r') as file:
        data = json.load(file)
    return data
settings = load_settings()

class ModObject(LimitedModObject):

    def __init__(self, mod_name="mod", version="0.0.1", description="", authors="", game="Isle Goblin", folder_name="Isle Goblin Playtest",
                 steampath="C:\\Program Files (x86)\\Steam\\steamapps\\common\\"):
        self.saved = False
        self.index = 0
        self.mod_maker_version = VERSION
        self.game = game
        global settings
        settings = load_settings()
        steampath = settings.get("Default Steam Directory", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\")
        self.folder_name = self.game if folder_name is None else folder_name
        self.steampath = steampath
        self.config_number = 0
        self.version = CodeLine(version, locked=True)
        self.description = description
        self.authors = authors
        self.mod_name = CodeLine(mod_name, locked=True)
        self.mod_name_no_space = CodeLine(mod_name.replace(" ", ""), locked=True)
        self.code = LargeCodeBlockWrapper()
        self.header = create_headers()
        self.code.insert_block_before(self.header)
        self.namespace = create_namespace(self.mod_name, self.mod_name_no_space)
        self.code.insert_block_after(self.namespace)
        self.in_namespace = create_namespace_contents(self.game)
        self.namespace.contents = self.in_namespace
        self.class_wrap = create_class(self.mod_name, self.mod_name_no_space)
        self.namespace.contents.insert_block_after(self.class_wrap)
        self.constants = create_constants(self.mod_name, self.mod_name_no_space, self.version)
        self.class_wrap.contents.insert_block_after(self.constants)
        self.config_entry_declarations = LargeCodeBlockWrapper()
        self.class_wrap.contents.insert_block_after(self.config_entry_declarations)
        self.config_definitions = LargeCodeBlockWrapper()
        self.class_wrap.contents.insert_block_after(self.config_definitions)
        self.reflections_declarations = LargeCodeBlockWrapper([LargeCodeBlockWrapper(), LargeCodeBlockWrapper()])
        # ^^ First is for methods second is for fields
        self.class_wrap.contents.insert_block_after(self.reflections_declarations)
        self.general_declarations = LargeCodeBlockWrapper()
        self.class_wrap.contents.insert_block_after(self.general_declarations)
        self.class_constructor = CodeBlockWrapper(
            prefix=CodeBlock([CodeLine("public "), self.mod_name_no_space, CodeLine("(){")], delimiter=""),
            contents=LargeCodeBlockWrapper(),
            postfix=end_block()
        )
        self.class_wrap.contents.insert_block_after(self.class_constructor)
        self.awake = create_awake(self.mod_name, self.mod_name_no_space)
        self.update = create_update(self.mod_name, self.mod_name_no_space)
        self.class_wrap.contents.insert_block_after(self.awake)
        self.class_wrap.contents.insert_block_after(self.update)
        self.add_config("mEnabled", "bool", "false", "Enable/Disable Mod",
                        "Controls if the mod should be enabled or disabled", should_indent=False)
        self.main_contents = self.class_wrap.contents
        self.indent()
        self.code.insert_block_after(CodeLine("\n"))

    def add_config(self, name, data_type, default, definition, description="", should_indent=True):
        if should_indent:
            self.config_entry_declarations.insert_block_after(
                CodeLine("public static ConfigEntry<" + data_type + "> " + name + ";").indent().indent())
            self.config_definitions.insert_block_after(CodeLine(
                "public ConfigDefinition " + name + "Def = new ConfigDefinition(pluginVersion, \"" + definition
                + "\");").indent().indent())
            self.class_constructor.contents.insert_block_after(CodeLine(
                name + " = " +
                "Config.Bind(" + name + "Def, " + default + ", new ConfigDescription(\"" + description +
                "\", null, new ConfigurationManagerAttributes {Order = " + str(self.config_number) + "}));"
            ).indent().indent().indent())
        else:
            self.config_entry_declarations.insert_block_after(
                CodeLine("public static ConfigEntry<" + data_type + "> " + name + ";"))
            self.config_definitions.insert_block_after(CodeLine(
                "public ConfigDefinition " + name + "Def = new ConfigDefinition(pluginVersion, \"" + definition
                + "\");"))
            self.class_constructor.contents.insert_block_after(CodeLine(
                name + " = " +
                "Config.Bind(" + name + "Def, " + default + ", new ConfigDescription(\"" + description +
                "\", null, new ConfigurationManagerAttributes {Order = " + str(self.config_number) + "}));"
            ))
        self.config_number -= 1

    def declare_variable(self, data_type, name, default=None):
        if default is not None:
            self.general_declarations.insert_block_after(CodeBlock([
                CodeLine("public"),
                CodeLine("static"),
                CodeLine(data_type),
                CodeLine(name),
                CodeLine("="),
                CodeLine(default + ";")
            ], delimiter=" ").indent().indent())
        else:
            self.general_declarations.insert_block_after(CodeBlock([
                CodeLine("public"),
                CodeLine("static"),
                CodeLine(data_type),
                CodeLine(name + ";")
            ], delimiter=" ").indent().indent())

    def create_harmony_patch(self, in_class, method, prefix=True, parameters=list(), have_instance=True, result=None):
        parameters = [i for i in parameters if i != '']
        if result is not None:
            parameters.insert(0, "ref " + result + " __result")
        if have_instance:
            parameters.insert(0, "ref " + in_class + " __instance")

        patch = LargeCodeBlockWrapper()
        self.main_contents.insert_block_after(patch)
        patch.insert_block_after(CodeLine(
            "[HarmonyPatch(typeof(" + in_class + "), \"" + method + "\")]"
        ))
        patch.insert_block_after(CodeLine(
            "[HarmonyPrefix]" if prefix else "[HarmonyPostfix]"
        ))
        patch.insert_block_after(CodeBlockWrapper(
            prefix=CodeLine(
                "private " + ("static " if not have_instance else "") + ("bool" if prefix else "void") + " " +
                in_class.replace("_", "") + method +
                ("Prefix" if prefix else "Postfix") +
                "Patch(" +
                ", ".join(parameters) + "){"
            ),
            contents=LargeCodeBlockWrapper(),
            postfix=end_block()
        ))
        return_false = CodeLine("return false; // Cancels Original Function" if prefix else "")
        return_true = CodeLine("return true;" if prefix else "")
        patch.block_list[-1].contents.insert_block_after(LargeCodeBlockWrapper([
            CodeBlockWrapper(
                prefix=CodeLine("if(mEnabled.Value){"),
                contents=CodeBlock([CodeLine("// Write code for patch here"),
                                    CodeLine("//__result = null;"), return_false]
                                   if result is not None else [CodeLine("// Write code for patch here"),
                                                               return_false]).indent(),
                postfix=end_block()
            ),
            return_true
        ]))
        patch.block_list[-1].contents.indent()
        patch.indent()
        patch.indent()
        return patch.block_list[-1].contents.block_list[-1].block_list[0].contents

    def autosave(self, changeSaved=True):
        current_directory = os.getcwd()
        name_no_space = self.mod_name_no_space.get_text()
        folder_path = os.path.join(current_directory, "projects/" + name_no_space)
        if not os.path.isdir(folder_path):
            return
        if changeSaved:
            self.saved = False

        save(self, location=folder_path + "/" + name_no_space + "-auto.igmm", overwrite_auto=False)

    def set_mod_name(self, new_name):
        self.mod_name.code = new_name
        self.mod_name_no_space.code = new_name.replace(" ", "")

    def set_version(self, new_version):
        self.version.code = new_version

    def set_authors(self, new_authors):
        self.authors = new_authors

    def get_text(self):
        return self.code.get_text()

    def get_code_lines(self):
        return self.code.get_code_lines()

    def get_block_list(self):
        return self.code.get_block_list()

    def get_list(self):
        return self.code.get_list()

    def indent(self):
        self.code.default_indent()

    def install(self, destroyonerror=None, progress_updater=print):
        progress_updater("Generating Dotnet Files...")
        path = create_files(self, destroyonerror=destroyonerror)
        if path is None:
            return None
        
        progress_updater("Running Dotnet Build...")
        build_result = dotnet_build(path)
        
        # Mod folder path with the mod name followed by the version
        mod_folder_name = f"{self.mod_name.get_text()}_{self.version.get_text()}"
        install_path = os.path.join(self.steampath, self.folder_name, "BepInEx/plugins")
        mod_install_path = os.path.join(install_path + "/" + mod_folder_name)
        
        try:
            # Create the folder if it doesn't exist
            os.makedirs(mod_install_path, exist_ok=True)
            
            # Move the compiled .dll file into the new mod folder
            shutil.move(
                os.path.join(path, "bin/Debug/netstandard2.1", self.mod_name_no_space.get_text() + ".dll"),
                os.path.join(mod_install_path, self.mod_name_no_space.get_text() + ".dll")
            )
            
            # Copy additional required libraries into the mod folder
            shutil.copyfile(
                os.path.join(os.getcwd(), "resources/Default Libraries/ConfigurationManager.dll"),
                os.path.join(install_path, "ConfigurationManager.dll")
            )
            shutil.copyfile(
                os.path.join(os.getcwd(), "resources/Default Libraries/netstandard.dll"),
                os.path.join(install_path, "netstandard.dll")
            )
            
            # Copy the manifest.json file to the mod folder
            shutil.copyfile(
                os.path.join(path, "manifest.json"),
                os.path.join(mod_install_path, "manifest.json")
            )
            
            # Copy the manifest.json file to the mod folder
            shutil.copyfile(
                os.path.join(path, "README.md"),
                os.path.join(mod_install_path, "README.md")
            )
            
            shutil.copyfile(
                os.path.join(path, "CHANGELOG.md"),
                os.path.join(mod_install_path, "CHANGELOG.md")
            )

        except FileNotFoundError:
            if destroyonerror is not None:
                destroyonerror.destroy()
            root = Tk()
            root.title("Build Failed")
            root.iconbitmap("resources/isle-goblin-mod-maker.ico")
            from tkinter import scrolledtext
            textbox = scrolledtext.ScrolledText(root)
            textbox.configure(bg="#191F44", fg="#FFC014")
            textbox.insert(1.0, build_result)
            textbox.pack(fill="both")
            root.update()
            global windows
            windows.append(root)
            root.focus()
            return None

        return True


def create_files(mod: ModObject, destroyonerror=None):
    global settings
    settings = load_settings()
    name_no_space = mod.mod_name_no_space.get_text()
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
    save(mod, location=folder_path + "/" + name_no_space + ".igmm")
    shutil.copyfile("resources/gitignoretemplate", folder_path + "/.gitignore")
    shutil.copyfile("resources/configmanagertemplate", folder_path + "/ConfigurationManagerAttributes.cs")
    with open(folder_path + "/" + name_no_space + ".cs", "w") as f:
        code = "\n".join([s for s in mod.code.get_text().splitlines() if s])
        f.write(code)
    with open(folder_path + "/" + name_no_space + ".csproj", "w") as f:
        code = open("resources/csprojtemplate", "r").read().replace("{{mod_name}}", name_no_space).replace("{{ptf}}", "")
        f.write(code)
        
    authors_list = mod.authors  # Get the comma-separated developers' names
    authors = [name.strip() for name in authors_list.split(",")] 

    manifest = {
        "mod_name": mod.mod_name.get_text(),
        "version": mod.version.get_text(),
        "description": mod.description,
        "mod_maker_version": mod.mod_maker_version,
        "authors": authors
    }

    with open(folder_path + "/manifest.json", "w") as json_file:
        json.dump(manifest, json_file, indent=4)
        
    readme_content = f"# {mod.mod_name.get_text()}\n\n" \
                     f"## Description\n{mod.description}\n\n" \
                     f"## Version\n{mod.version.get_text()}\n\n" \
                     f"## Developers\n{', '.join(authors)}\n\n" \
                     f"## Requirements\nThis mod requires BepInEx installed.\n\n" \
                     f"## Installation\n1. Launch the game.\n2. Enable the mod and play!"

    with open(folder_path + "/README.md", "w") as readme_file:
        readme_file.write(readme_content)
        
    changelog_path = folder_path + "/CHANGELOG.md"
    changelog_entry = f"## v{mod.version.get_text()} - {datetime.now().strftime('%Y-%m-%d')}\n" \
                      f"- [ADD CHANGES].\n"

    if os.path.exists(changelog_path):
        with open(changelog_path, "a") as changelog_file:  # Use 'a' to append
            changelog_file.write("\n" + changelog_entry)
    else:
        with open(changelog_path, "w") as changelog_file:
            changelog_file.write("# Changelog\n\n" + changelog_entry)
        
    try:

        shutil.copytree(os.path.join(mod.steampath, mod.folder_name, mod.game + "_Data", "Managed"),
                        folder_path + "\\Libraries", dirs_exist_ok=True)
        shutil.copytree(os.path.join(mod.steampath, mod.folder_name, "BepInEx/core"),
                        folder_path + "\\Libraries", dirs_exist_ok=True)
        shutil.copytree(os.path.join(os.getcwd(), "resources/Default Libraries"),
                        folder_path + "\\Libraries", dirs_exist_ok=True)
    except FileNotFoundError as e:
        print(e)
        print("ERROR: Could not create mod files, make sure " + mod.game + " is installed with BepInEx")
        if destroyonerror is not None:
            destroyonerror.destroy()
        messagebox.showerror("Could Not Create Mod Files",
                             "Couldn't Create Mod File, Make sure " + mod.game + " is installed with BepInEx")
        return None
    return folder_path


def dotnet_build(path):
    command = subprocess.Popen(["dotnet", "build"], cwd=path, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    return command.stdout.read()


def save(mod_object, location="mod.igmm", overwrite_auto=True):
    mod_object.saved = True
    auto_path = location.split(".")
    if len(auto_path) == 1:
        auto_path += "-auto"
    else:
        auto_path[-2] += "-auto"
        auto_path = ".".join("auto_path")
    if overwrite_auto:
        if os.path.exists(auto_path):
            os.remove(auto_path)
    pickle.dump(mod_object, open(location, "wb"))


def load(location="mod.igmm", auto_option=True):
    auto_path = location.split(".")
    if len(auto_path) == 1:
        auto_path += "-auto"
    else:
        auto_path[-2] += "-auto"
        auto_path = ".".join(auto_path)
    use_auto = False
    if auto_option and os.path.exists(auto_path):
        use_auto = messagebox.askquestion("Load Autosave?",
                                          "There is an autosave available, would you like to load it instead?")
    if use_auto:
        location = auto_path
    mod = pickle.load(open(location, "rb"))
    if mod.mod_maker_version != VERSION:
        messagebox.showwarning("Mod From Old Version", "This Mod Was Made in Version " + mod.mod_maker_version +
                               " and may not function properly when converted to this version (" + VERSION + ")")
        mod.mod_maker_version = VERSION
    return mod


def copy(mod_object, name):
    name_no_space = name.replace(" ", "")
    current_directory = os.getcwd()
    folder_path = os.path.join(current_directory, "projects", name_no_space)
    try:
        os.mkdir(folder_path)
    except FileExistsError:
        return "That Project Already Exists"
    save(mod_object, location=folder_path + "/" + name_no_space + ".igmm")
    mod2 = load(folder_path + "/" + name_no_space + ".igmm")
    mod2.set_mod_name(name)
    save(mod2, location=folder_path + "/" + name_no_space + ".igmm")

def get_system_architecture():
    architecture = platform.architecture()[0]
    if '64' in architecture:
        return 'x64'
    return 'x86'


def get_bepinex_download_url(architecture):
    base_url = "https://github.com/BepInEx/BepInEx/releases/download/v5.4.23.2/BepInEx"
    os_system = platform.system()
    bepinex_url = ""
    if os_system == "Windows":
        bepinex_url = f"{base_url}_win_{architecture}_5.4.23.2.zip"  
    elif os_system == "Linux":
        bepinex_url = f"{base_url}_linux_{architecture}_5.4.23.2.zip"
    elif os_system == "Darwin":  # macOS
        bepinex_url = f"{base_url}_macos_x64_5.4.23.2.zip"
    else:
        messagebox.showerror("Error", "Unsupported operating system detected.")
        return False
    return bepinex_url

def download_file(url, dest_path):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(dest_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

def extract_zip(file_path, extract_to):
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def prompt_for_custom_steam_directory(cursteampath):
    root = Tk()
    root.withdraw()  # Hide the root window
    steam_path = filedialog.askdirectory(initialdir=settings.get("Default Steam Directory", cursteampath), title="Select Steam Library Directory")
    if steam_path and os.path.exists(os.path.join(steam_path, "steamapps", "common")):
        return steam_path
    return None


def find_steam_directory(folder_name):
    # First, attempt to get the Steam directory from the registry
    steam_path = get_steam_directory()
    if steam_path and os.path.exists(os.path.join(steam_path, "steamapps", "common", folder_name)):
        return steam_path

    # Check common custom drive locations
    common_drives = ["C:", "D:", "E:", "F:", "Z:"]
    for drive in common_drives:
        possible_path = os.path.join(drive, "SteamLibrary", "steamapps", "common")
        if os.path.exists(os.path.join(possible_path, folder_name)):
            return possible_path
        
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

def verify_game(name, folder_name, steam_path, prompt):
    architecture = get_system_architecture()
    download_url = get_bepinex_download_url(architecture)
    dest = os.path.join(os.getcwd(), "resources/BepInEx.zip")
    # zip_path = os.path.join(os.getcwd(), f"BepInEx_{version}_{architecture}.zip")
    
    if not os.path.isdir(os.path.join(steam_path, folder_name)):
        # Try to find the correct Steam directory
        steam_path = find_steam_directory(folder_name)
        if not steam_path:
            messagebox.showerror("Game Not Found",
                                 f"Game Not Found. There is no directory \"{os.path.join(steam_path, folder_name)}\"",
                                 parent=prompt)
            return False
        with open("settings.json", 'r') as file:
            settings = json.load(file)
        
        settings["Default Steam Directory"] = steam_path
        
        with open("settings.json", 'w') as file:
            json.dump(settings, file, indent=4)
        return True
    if not os.path.isdir(os.path.join(steam_path, folder_name, name + "_Data")):
        messagebox.showerror("Game Not Valid",
                             "The directory \"" + os.path.join(steam_path, folder_name, name + "_Data") +
                             "\" Does not exist, this is probably due to the game not being a CSharp Unity Game which "
                             "means it can't be modded with this tool", parent=prompt)
        return False
    if not os.path.isdir(os.path.join(steam_path, folder_name, "BepInEx")):
        question = messagebox.askquestion("Install BepInEx",
                                          "BepInEx is not installed on this game, would you like to install it "
                                          "automatically?",
                                          icon="info", parent=prompt)
        if question == "yes":
            # shutil.copytree(os.path.join(os.getcwd(), "resources", "BepInEx"),
            #                 os.path.join(steam_path, folder_name), dirs_exist_ok=True)
            # download_bepinex(bepinex_url, os.path.join(steam_path, folder_name))
            download_file(download_url, dest)
            extract_zip(dest, os.path.join(steam_path, folder_name))
            messagebox.showinfo("BepInEx Installed", "BepInEx has been installed, please run the game once and then "
                                                     "exit in order to generate the proper files, then click \"OK\"",
                                parent=prompt)
            if not os.path.isdir(os.path.join(steam_path, folder_name, "BepInEx", "Plugins")):
                return "BepInEx not fully installed"
            return True
        else:
            return False
    if not os.path.isdir(os.path.join(steam_path, folder_name, "BepInEx", "Plugins")):
        messagebox.showinfo("BepInEx Partially Installed",
                            "BepInEx is installed with files missing, please run the game once and then "
                            "exit in order to generate the proper files, then click \"OK\"",
                            parent=prompt)
        if not os.path.isdir(os.path.join(steam_path, folder_name, "BepInEx", "Plugins")):
            return "BepInEx not fully installed"
    return True


if __name__ == "__main__":
    print("WRONG SCRIPT")