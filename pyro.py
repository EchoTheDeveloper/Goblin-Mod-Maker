#!/usr/bin/env python


"""
    GMMpyro, modified to work with the Goblin Mod Maker, an extension of UnityModderPyro, Modified to work for Unity Mod Maker By Hippolippo

    Original Code https://github.com/JamesStallings/pyro/blob/master/pyro:
    simple elegant text editor built on python/tkinter
    by James Stallings, June 2015
    Adapted from:

      Pygments Tkinter example
      copyleft 2014 by Jens Diemer
      licensed under GNU GPL v3

    and

      'OONO' designed and written by Lee Fallat, 2013-2014.
      Inspired by acme, sam, vi and ohmwriter.
    A sincere thanks to these good people for making their source code available for myself and others
    to learn from. Cheers!


        Pyro currently does a very minimalist job of text editing via tcl/tk ala tkinter.

        What pyro does now:

           colorizes syntax for a variety of text types; to wit:

               Python
               PlainText
               Html/Javascript
               Xml
               Html/Php
               Perl6
               Ruby
               Ini/Init
               Apache 'Conf'
               Bash Scripts
               Diffs
               C#
               MySql

           writes out its buffer
           converts tabs to 4 spaces

           It does this in an austere text editor framework which is essentially a glue layer
           bringing together the tk text widget with the Pygment library for styling displayed
           text. Editor status line is in the window title.

           Pyro comes with one serious warning: it is a user-space editor. It makes no effort
           to monitor state-change events on files and so should not be used in situations
           where it is possible that more than one writer will have access to the file.


        Pyro's current controls are as follows:

           Ctrl+q quits
           Ctrl+w writes out the buffer
           Selection, copy, cut and paste are all per xserver/window manager. Keyboard navigation via
           arrow/control keys, per system READLINE.

        Pyro's current commands are:

           #(num) move view to line 'num' and highlight it, if possible.
           *(text) find text in file.
           /(delim)(text)(delim)(text) search and replace

        Pyro requires Tkinter and Pygment external libraries.

"""

RECENT = None

import os
import io
import sys

import ChangeManager
from GraphicalInterface import *
import MenuMethods
from functools import partial
import time

try:
    # Python 3
    import tkinter
    from tkinter import font, ttk, scrolledtext, _tkinter, simpledialog
except ImportError:
    # Python 2
    import Tkinter as tkinter
    from Tkinter import ttk
    import tkFont as font
    import ScrolledText as scrolledtext

from ModObject import *
from pygments.lexers.python import PythonLexer
from pygments.lexers.special import TextLexer
from pygments.lexers.html import HtmlLexer
from pygments.lexers.html import XmlLexer
from pygments.lexers.templates import HtmlPhpLexer
from pygments.lexers.perl import Perl6Lexer
from pygments.lexers.ruby import RubyLexer
from pygments.lexers.configs import IniLexer
from pygments.lexers.configs import ApacheConfLexer
from pygments.lexers.shell import BashLexer
from pygments.lexers.diff import DiffLexer
from pygments.lexers.dotnet import CSharpLexer
from pygments.lexers.sql import MySqlLexer

from pygments.styles import get_style_by_name
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import queue
import threading

pyros = []
windows = []
core_ui = None
open_files = {}
last_opened_file = None


def load_theme(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return data

def load_settings():
    with open("settings.json", 'r') as file:
        data = json.load(file)
    return data

def refresh_theme():
    global InterfaceMenu_Background, InterfaceMenu_Geometry, InterfaceMenu_NewButtonBackground, InterfaceMenu_OpenButtonBackground
    global InterfaceMenu_MouseEnter, InterfaceMenu_MouseExit, InterfaceMenu_ButtonConfigFG, InterfaceMenu_ButtonConfigBG
    global PyroPrompt_Background, PyroPrompt_Foreground, PyroPrompt_WarningTextColor, PyroPrompt_Selected
    global NewButton, OpenButton
    global Click, Hover

    # Reload the theme data
    settings = load_settings()
    theme_data = load_theme('resources/themes/' + settings.get("Selected Theme", "Isle Goblin") + ".json")
    
    # Update global theme variables
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
    PyroPrompt_Selected = theme_data.get("pyroprompt", {}).get("selected", "")
    Click = theme_data.get("click", "")
    Hover = theme_data.get("hover", "")

class LineNumbers(Text):  # scrolledtext.ScrolledText
    def __init__(self, master, text, **kwargs):
        super().__init__(master, **kwargs)
        self.text = text
        self.text.bind('<KeyRelease>', self.match_up)
        self.num_of_lines = -1
        self.insert(1.0, '1')
        self.configure(state='disabled')

    def match_up(self, e=None):
        p, q = self.text.index("@0,0").split('.')
        p = int(p)
        
        # Get the final index without counting the trailing newline
        final_index = str(self.text.index(tkinter.END + "-1c"))
        temp = self.num_of_lines
        self.num_of_lines = final_index.split('.')[0]
        
        # Generate line numbers string
        line_numbers_string = "\n".join(str(1 + no) for no in range(int(self.num_of_lines)))
        width = len(str(self.num_of_lines)) + 3

        # Update line numbers text
        self.configure(state='normal', width=width)
        if self.num_of_lines != temp:
            self.delete(1.0, tkinter.END)
            self.insert(1.0, line_numbers_string)
        self.configure(state='disabled')
        
        # Sync scrolling
        self.scroll_data = self.text.yview()
        self.yview_moveto(self.scroll_data[0])


class FileTreeview:
    def __init__(self, master, core_ui, mod_name_no_space, **uiopts):
        self.core_ui = core_ui
        self.master = master
        self.mod_name_no_space = mod_name_no_space
        self.update_queue = queue.Queue()

        # Create a Frame for the Treeview and button layout
        self.tree_frame = Frame(master)
        self.tree_frame.grid(column=0, row=0, sticky='nsew', padx=(5, 0), pady=5)
        refresh_theme()


        # Create and configure the Treeview inside the Frame
        self.tree = ttk.Treeview(self.tree_frame, **uiopts)
        self.setup_treeview_style()
        self.setup_treeview()

        # Create the "New File" button and place it over the Treeview header
        # self.new_file_button = Button(self.tree_frame, text="+", command=self.on_new_file_button_click, relief="flat", width=2)
        # self.new_file_button.place(relx=1.0, rely=0.0, anchor="ne", x=-25, y=0)

        # Horizontal Scrollbar for TreeView
        self.xsb = Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=self.xsb.set)
        self.xsb.grid(row=1, column=0, sticky="ew")

        # Vertical Scrollbar for TreeView
        self.ysb = Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.ysb.set)
        self.ysb.grid(row=0, column=1, sticky="ns")

        self.xsb.configure(bg=PyroPrompt_Background, troughcolor="gray", highlightthickness=0)
        self.ysb.configure(bg=PyroPrompt_Background, troughcolor="gray", highlightthickness=0)

        # Ensure Treeview fills its parent Frame
        self.tree.grid(row=0, column=0, sticky='nsew')

        # Adjust column and row configuration of the frame
        self.tree_frame.grid_columnconfigure(0, weight=1)  # Expand to fill available space
        self.tree_frame.grid_rowconfigure(0, weight=1)  # Expand to fill available space

        # Ensure Treeview's column and row weights are set for proper expansion
        self.tree_frame.grid_columnconfigure(1, weight=0)  # Scrollbar column
        self.tree_frame.grid_rowconfigure(1, weight=0)  # Scrollbar row

        self.folderpath = os.path.join(os.getcwd(), "projects", self.mod_name_no_space.get_text(), "Files")
        self.event_handler = self.FileChangeHandler(self.update_queue)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.folderpath, recursive=True)
        self.observer.start()

        self.master.after(100, self.process_updates)

        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)

    # Button click event handler (empty logic, you can fill this in later)
    def on_new_file_button_click(self):
        pass

    def setup_treeview_style(self):
        # Create a style for the Treeview
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("Treeview",
                        background=PyroPrompt_Background,  # Background color for Treeview items
                        foreground=PyroPrompt_Foreground,  # Text color for Treeview items
                        fieldbackground=InterfaceMenu_MouseEnter,  # Field background color
                        bordercolor=PyroPrompt_Background)  # Border color
        
        # Add hover effects and selection color
        style.map("Treeview",
                background=[("selected", PyroPrompt_Selected)],  # Color when an item is selected
                foreground=[("selected", PyroPrompt_Foreground)],  # Text color when selected
                fieldbackground=[("hover", InterfaceMenu_MouseEnter)],  # Background on hover
                highlightcolor=[("hover", "#45d6cf")])  # Highlight color on hover
        
        # Ensure the headers and scrollbars match the theme
        style.configure("Treeview.Heading",
                        background=PyroPrompt_Background,  # Background for headers
                        foreground=PyroPrompt_Foreground,  # Header text color
                        bordercolor=InterfaceMenu_MouseEnter,
                        relief="flat")
        
        # style.configure("Horizontal.TScrollbar", background=PyroPrompt_Background)
        # style.configure("Vertical.TScrollbar", background=PyroPrompt_Background)

        # Apply this style to the treeview
        self.tree.configure(style="Treeview")
        
        self.tree.tag_configure('row', background=InterfaceMenu_MouseEnter, foreground=PyroPrompt_Foreground)
        
        style.configure("Treeview.Column",
                        background=PyroPrompt_Background,  # Background for headers
                        foreground=PyroPrompt_Foreground,  # Header text color
                        bordercolor=InterfaceMenu_MouseEnter,
                        relief="flat")

    def setup_treeview(self):
        self.tree.delete(*self.tree.get_children())  # Clear existing content

        # Define the folder and file paths
        current_directory = os.getcwd()
        folderpath = os.path.join(current_directory, "projects", self.mod_name_no_space.get_text(), "Files")

        # Create the main folder if it doesn't exist
        if not os.path.isdir(folderpath):
            os.makedirs(folderpath)

        # Add the root folder
        self.tree.insert("", "end", "Files", text="Files")

        # Populate the Treeview with files and folders
        self.populate_treeview("Files", folderpath)
        self.adjust_column_width()  # Adjust column width after populating
        
        self.expand_folder("Files")
        
    def expand_folder(self, folder_id):
        self.tree.item(folder_id, open=True)  # Open the folder

    def populate_treeview(self, parent, path):
        for name in os.listdir(path):
            item_path = os.path.join(path, name)
            if os.path.isdir(item_path):
                # Add folder and populate it
                folder_id = self.tree.insert(parent, "end", name, text=name)
                self.populate_treeview(folder_id, item_path)
            else:
                # Add file
                self.tree.insert(parent, "end", name, text=name)

    def adjust_column_width(self):
        # Define base values for padding and padding per character
        base_padding_per_char = 50
        base_additional_padding = 120

        # Define scaling factors
        length_threshold = 45
        scaling_factor = 4
        
        # Calculate the maximum number of characters in any item
        max_length = max(len(self.tree.item(item, "text")) for item in self.tree.get_children())
        
        # Scale padding per character and additional padding based on length
        if max_length > length_threshold:
            padding_per_char = base_padding_per_char * scaling_factor
            additional_padding = base_additional_padding * scaling_factor
        else:
            padding_per_char = base_padding_per_char
            additional_padding = base_additional_padding
        
        # Calculate the column width based on the maximum length and character width
        max_width = max_length * padding_per_char
        
        # Add some padding for better appearance
        new_width = max_width + additional_padding
        if new_width < 225:
            new_width = 225
        
        self.tree.column("#0", minwidth=new_width)

    def refresh_treeview(self):
        self.update_queue.put("refresh")

    def process_updates(self):
        while not self.update_queue.empty():
            message = self.update_queue.get()
            if message == "refresh":
                self.setup_treeview()
        self.master.after(100, self.process_updates)

    def on_item_select(self, event):
        # Get the item that was clicked
        item = self.tree.selection()
        if not item:
            return
        
        # Get the file path for the selected item
        file_path = self.get_file_path(item[0])
        if file_path and os.path.isfile(file_path):
            self.core_ui.loadfile(file_path)

    def get_file_path(self, item_id):
        return os.path.join(self.folderpath, item_id)

    class FileChangeHandler(FileSystemEventHandler):
        def __init__(self, update_queue):
            self.update_queue = update_queue

        def on_modified(self, event):
            self.update_queue.put("refresh")

        def on_created(self, event):
            self.update_queue.put("refresh")

        def on_deleted(self, event):
            self.update_queue.put("refresh")

        def on_moved(self, event):
            self.update_queue.put("refresh")


class CoreUI(object):
    """
        CoreUI is the editor object, derived from class 'object'. It's instantiation initilizer requires the
        ubiquitous declaration of the 'self' reference implied at call time, as well as a handle to
        the lexer to be used for text decoration.
    """

    def __init__(self, lexer, filename="Untitled", filepath=None, mod=None, settings={}):
        global core_ui
        core_ui = self
        self.settings = settings
        set_window_count(get_window_count() + 1)
        self.filename = filename
        if mod is None:
            mod = ModObject("Untitled")
        self.mod = mod
        self.contents = mod.get_text()
        self.sourcestamp = {}
        self.filestamp = {}
        self.uiopts = []
        self.lexer = lexer
        self.lastRegexp = ""
        self.markedLine = 0
        self.root = tkinter.Tk()
        self.root.withdraw()
        self.root.iconbitmap("resources/goblin-mod-maker.ico")
        self.root.protocol("WM_DELETE_WINDOW", self.destroy_window)
        self.bootstrap = []
        self.modified = False
        
        # Call uiconfig to set up the UI
        if filepath:
            self.filepath = filepath
        # current_directory = os.getcwd()
        self.uiconfig()
        
        if self.filepath and os.path.isfile(self.filepath):
            self.loadfile(self.filepath)
        # Ensure text is set before using it
        if not hasattr(self, 'text'):
            try:
                self.loadfile(self.filepath)
            except:
                raise RuntimeError("Text widget not initialized")
        global RECENT
        RECENT = self
        self.root.bind("<Key>", self.event_key)
        self.root.bind('<Control-KeyPress-q>', self.close)
        self.root.bind("<Control-KeyPress-s>", self.save_file_key_press)
        self.root.bind('<Control-Shift-T>', self.open_last_file)
        # self.root.bind('<Control-KeyPress-f>', MenuMethods.openSearch(self)) DOESNT WORK CURRENTLY
        self.root.bind('<Button>', self.event_mouse)
        self.root.bind('<Configure>', self.event_mouse)
        
        self.root.geometry("1200x700+10+10")
        self.initialize_menubar()
        self.updatetitlebar()
        self.starting()
        global pyros
        pyros.append(self)
        self.search_done = False
        self.search_regexp = None

        def load_file(filename):
            with open(filename, 'r') as file:
                data = json.load(file)
            return data

        self.keywords = load_file("resources/keywords.json")

        # Define snippets
        self.snippets = load_file("resources/snippets.json")
        self.autocomplete_window = None

    def open_last_file(self, e):
        global last_opened_file
        self.loadfile(last_opened_file)

    def save_file(self, filepath=None):
        """Save the current contents to a file."""
        if filepath is None:
            filepath = self.filepath
        else:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as file:
                file.write(self.text.get('1.0', tkinter.END))
            self.filepath = filepath
            self.modified = False 
            filename = os.path.basename(self.filepath)
            self.notebook.tab(self.notebook.select(), text=filename) 
            self.updatetitlebar()
            
    def sort_and_save_open_files(self):
        """Sort and save the contents of all open files in the Notebook."""
        # Create a list of filenames from open_files dictionary
        filenames = list(open_files.keys())
        
        # Sort filenames (you can customize the sorting criteria here)
        sorted_filenames = sorted(filenames)
        
        # Save each file's content
        for filename in sorted_filenames:
            text_widget, tab = open_files[filename]  # Retrieve the associated text widget
            # Use the text widget to get the content and save it to the file
            content = text_widget.get('1.0', tkinter.END)
            with open(filename, 'w') as file:
                file.write(content)
            revised_filename = os.path.basename(filename)
            self.notebook.tab(tab, text=revised_filename) 
            self.updatetitlebar()
    
    def undo(self, e=None, text_widget=None):
        mod = ChangeManager.undo()
        if mod is not None:
            self.mod = mod
            self.refresh(updateMod=False)  # refresh with updateMod=False to prevent overwriting the mod
        return "break"

    def redo(self, e=None, text_widget=None):
        mod = ChangeManager.redo()
        if mod is not None:
            self.mod = mod
            self.refresh(updateMod=False)  # refresh with updateMod=False to prevent overwriting the mod
        return "break"

    def save_file_key_press(self, e):
        self.save_file(self.filepath)
    
    def initialize_menubar(self):
        self.menubar = tkinter.Menu(self.root)

        self.filemenu = tkinter.Menu(self.menubar, tearoff=False)
        self.editmenu = tkinter.Menu(self.menubar, tearoff=False)
        self.createmenu = tkinter.Menu(self.menubar, tearoff=False)
        self.buildmenu = tkinter.Menu(self.menubar, tearoff=False)
        self.toolsmenu = tkinter.Menu(self.menubar, tearoff=False)

        # -------------------Sub Menus------------------------
        self.snippetsmenu = tkinter.Menu(self.menubar, tearoff=False)


        self.menubar.add_cascade(label="File", menu=self.filemenu)

        self.filemenu.add_command(label="New Mod", command=partial(MenuMethods.new, self))
        self.filemenu.add_command(label="Open", command=partial(MenuMethods.open, self.settings))
        self.filemenu.add_command(label="Save", command=partial(MenuMethods.save, self, self.filepath))
        self.filemenu.add_command(label="Save as Renamed Copy", command=partial(MenuMethods.copy, self))
        self.filemenu.add_command(label="Save C# File", command=partial(self.save_file, self.filepath)) 
        self.filemenu.add_command(label="New File", command=partial(MenuMethods.new_file, self))
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Close", command=self.close)



        self.menubar.add_cascade(label="Edit", menu=self.editmenu)

        self.editmenu.add_command(label="Change Mod Name", command=partial(MenuMethods.change_mod_name, self))
        self.editmenu.add_command(label="Change Mod Version",command=partial(MenuMethods.change_mod_version, self))
        self.editmenu.add_command(label="Change Mod Developers",command=partial(MenuMethods.change_mod_authors, self))
        self.editmenu.add_separator()
        self.editmenu.add_command(label="Undo", command=self.undo)
        self.editmenu.add_command(label="Redo", command=self.redo)
        self.editmenu.add_separator()
        self.editmenu.add_command(label="Cut", command=self.cut)
        self.editmenu.add_command(label="Copy", command=self.copy)
        self.editmenu.add_command(label="Paste", command=self.paste)


        self.menubar.add_cascade(label="Create", menu=self.createmenu)

        self.createmenu.add_command(label="Create Harmony Patch", command=partial(MenuMethods.create_harmony_patch, self))
        self.createmenu.add_command(label="Create Config Item", command=partial(MenuMethods.create_config_item, self))
        self.createmenu.add_command(label="Create Keybind", command=partial(MenuMethods.create_keybind, self))
        self.createmenu.add_command(label="Create NPC Asset", command=partial(MenuMethods.create_npc_data_asset, self))



        self.menubar.add_cascade(label="Build", menu=self.buildmenu)

        self.buildmenu.add_command(label="Build and Install", command=partial(MenuMethods.build_install, self))
        self.buildmenu.add_command(label="Generate Dotnet Files", command=partial(MenuMethods.export_dotnet, self))


        self.menubar.add_cascade(label="Tools", menu=self.toolsmenu)

        self.toolsmenu.add_command(label="Search", command=partial(MenuMethods.openSearch, self))
        # self.toolsmenu.add_command(label="Search and Replace", command=self.replace)
        self.toolsmenu.add_command(label="Go To Line", command=partial(MenuMethods.openGTL, self))

        self.snippetsmenu.add_command(label="Go To Line", command=partial(MenuMethods.openGTL, self))


        self.root.config(menu=self.menubar)
    
    #-------------------- START Autocomplete and Snippets START --------------------#
    def on_key_release(self, event):
        if event.keysym in ["Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Tab"]:
            return  # Ignore modifier keys and Tab

        if event.keysym == "space":
            return  # Ignore space key to prevent triggering autocomplete again

        self.show_autocomplete()

    def show_autocomplete(self):
        self.hide_autocomplete()  # Hide previous autocomplete if it exists

        cursor_position = self.text.index(INSERT)
        line_text = self.text.get(f"{cursor_position} linestart", cursor_position)
        current_word = line_text.split()[-1] if line_text.split() else ""

        if not current_word:
            return

        suggestions = []

        # Add snippets if any match the current word
        if current_word in self.snippets:
            snippet_preview = self.snippets[current_word][:8] + "..."
            suggestions.append((current_word, f"{current_word}: ({snippet_preview})"))

        # Add keywords that start with the current word
        keyword_suggestions = [kw for kw in self.keywords if kw.startswith(current_word)]
        suggestions.extend([(kw, kw) for kw in keyword_suggestions])

        if suggestions:
            self.autocomplete_window = Toplevel(self.root)
            self.autocomplete_window.wm_overrideredirect(True)
            self.autocomplete_window.lift()  # Ensure it stays on top
            self.autocomplete_window.configure(background=PyroPrompt_Background)
            self.text.focus_set()  # Ensure it takes focus

            x, y, _, _ = self.text.bbox(INSERT)
            x += self.text.winfo_rootx()
            y += self.text.winfo_rooty() + 25

            self.autocomplete_window.geometry(f"+{x}+{y}")

            self.suggestion_listbox = Listbox(
                self.autocomplete_window,
                selectmode=SINGLE,
                height=min(len(suggestions), 6),
                foreground=PyroPrompt_Foreground,
                background=PyroPrompt_Background
            )
            self.suggestion_listbox.pack()

            for _, display_text in suggestions:
                self.suggestion_listbox.insert(END, display_text)

            # Bind Listbox events
            self.suggestion_listbox.bind("<Double-1>", lambda e: self.insert_autocomplete())
            self.suggestion_listbox.bind("<Return>", lambda e: self.insert_autocomplete())
            self.suggestion_listbox.bind("<Up>", self.on_arrow_key_in_listbox)
            self.suggestion_listbox.bind("<Down>", self.on_arrow_key_in_listbox)

            # Ensure Listbox receives focus
            # self.suggestion_listbox.focus_set()

            # Bind click outside the autocomplete window to hide it
            self.suggestion_listbox.insert(END, display_text)
        
        # Automatically select the first suggestion
            self.suggestion_listbox.selection_set(0)
            self.suggestion_listbox.activate(0)
            self.root.bind("<Button-1>", self.on_click_outside)

    def insert_autocomplete(self, e):
        if not self.suggestion_listbox:
            return

        selected_text = self.suggestion_listbox.get(ACTIVE)
        cursor_position = self.text.index(INSERT)
        line_text = self.text.get(f"{cursor_position} linestart", cursor_position)
        current_word = line_text.split()[-1] if line_text.split() else ""

        self.text.delete(f"{cursor_position} - {len(current_word)}c", cursor_position)

        # Determine if the selected item is a snippet or a keyword
        if ':' in selected_text:
            # Extract the original word part from the selected text
            original_word = selected_text.split(':')[0]
            if original_word in self.snippets:
                self.text.insert(INSERT, self.snippets[original_word])
        else:
            # Insert the keyword directly
            self.text.insert(INSERT, selected_text)

        self.hide_autocomplete()

    def accept_autocomplete_or_snippet(self, event):
        cursor_position = self.text.index(INSERT)
        line_start = f"{cursor_position} linestart"
        line_text = self.text.get(line_start, cursor_position)

        current_word = line_text.split()[-1] if line_text.split() else ""

        selected_indices = self.suggestion_listbox.curselection()

        if selected_indices:
            selected_index = selected_indices[0]
            selected_suggestion = self.suggestion_listbox.get(selected_index)

            # If the selected suggestion contains a colon, treat it as a snippet
            if ':' in selected_suggestion:
                keyword = selected_suggestion.split(':')[0].strip()
                text_to_insert = self.snippets.get(keyword, selected_suggestion)  # Default to the suggestion if not found
            else:
                text_to_insert = selected_suggestion

            # Replace the current word with the selected text to insert
            self.text.delete(f"{cursor_position} - {len(current_word)}c", cursor_position)
            self.text.insert(INSERT, text_to_insert)

            self.hide_autocomplete()
            return "break"  # Prevent default behavior

    def on_arrow_key(self, event):
        if self.autocomplete_window:
            if event.keysym in ("Up", "Down"):
                # Prevent default behavior of moving cursor in the text widget
                return "break"

    def on_arrow_key_in_listbox(self, event):
        if not self.suggestion_listbox:
            return

        if event.keysym not in ("Up", "Down"):
            return

        current_selection = self.suggestion_listbox.curselection()
        if event.keysym == "Up":
            if current_selection:
                index = current_selection[0] - 1
            else:
                index = self.suggestion_listbox.size() - 1
        elif event.keysym == "Down":
            if current_selection:
                index = current_selection[0] + 1
            else:
                index = 0

        index = max(0, min(self.suggestion_listbox.size() - 1, index))
        self.suggestion_listbox.selection_clear(0, END)
        self.suggestion_listbox.selection_set(index)
        self.suggestion_listbox.activate(index)
        self.suggestion_listbox.see(index)

        # Ensure Listbox retains focus
        self.suggestion_listbox.focus_set()
        return "break"  # Prevent further propagation of the event

    def on_click_outside(self, event):
        if self.autocomplete_window and not self.autocomplete_window.winfo_containing(event.x_root, event.y_root):
            self.hide_autocomplete()

    def on_space_press(self, event):
        if self.autocomplete_window:
            self.hide_autocomplete()

    def hide_autocomplete(self, event=None):
        if self.autocomplete_window:
            self.autocomplete_window.destroy()
            self.autocomplete_window = None
            self.root.unbind("<Button-1>")   # Unbind click outside event
    #-------------------- END Autocomplete and Snippets END --------------------#

    def refresh(self, updateMod=True):
        if updateMod:
            self.scroll_data = self.text.yview()
            text = self.text.get("1.0", tkinter.END)[:-1]
            cursor = self.text.index(tkinter.INSERT)
            # print(cursor)
            index = ChangeManager.update(self.mod, self.text.get("1.0", tkinter.END)[:-1])
            if index == "Locked":
                self.undo()
                return
            self.mod.index = index
        else:
            text = None
            index = self.mod.index
        self.recolorize(self.text)
        # self.root.update()
        self.text.yview_moveto(self.scroll_data[0])

    def uiconfig(self):
        """
        This method sets up the main window and two text widgets (the editor widget, and a
        text entry widget for the commandline).
        """
        self.uiopts = {
            "height": 1000,
            "width": 1000,
            "cursor": "xterm",
            "bg": "#0d1117",
            "fg": "#FFAC00",
            "insertbackground": "#FFD310",
            "insertborderwidth": 1,
            "insertwidth": 3,
            "exportselection": True,
            "undo": True,
            "selectbackground": "#E0000E",
            "inactiveselectbackground": "#E0E0E0",
        }
        
        # Treeview UI options
        treeview_uiopts = {
            "columns": ["1"],  # Adjust columns as needed
            "show": "tree"
        }
        
        # Create FileTreeview instance
        self.file_treeview = FileTreeview(self.root, self, self.mod.mod_name_no_space, **treeview_uiopts)
        # Ensure Treeview column width is set and adjust if needed
        self.file_treeview.tree.column("#0", width=50, minwidth=350, stretch=True)  # Adjust width as needed
        # Add Treeview to the grid
        self.file_treeview.tree.grid(row=0, column=0, sticky=(N, S, E, W))
        
        closedir = os.path.join("resources", "imgs", "close")
        self.i1 = PhotoImage(file=os.path.join(closedir, "close.gif"))
        self.i2 = PhotoImage(file=os.path.join(closedir, "close_active.gif"))
        self.i3 = PhotoImage(file=os.path.join(closedir, "close_pressed.gif"))
        style = ttk.Style()
        style.configure("ButtonNotebook.TNotebook", background="#0d1117", borderwidth=0)
        style.map("ButtonNotebook.TNotebook", background=[("selected", "#1c1e22")])  # Change background when selected
        style.element_create("close", "image", self.i1,
            ("active", "pressed", "!disabled", self.i3),
            ("!active", "!disabled", self.i1),  
            ("hover", "!disabled", self.i2),  
            border=8, sticky='')
        style.layout("ButtonNotebook.Tab", [
            ("ButtonNotebook.tab", {"sticky": "nswe", "children":
                [("ButtonNotebook.padding", {"side": "top", "sticky": "nswe",
                    "children":
                    [("ButtonNotebook.focus", {"side": "top", "sticky": "nswe",
                        "children":
                        [("ButtonNotebook.label", {"side": "left", "sticky": ''}),
                        ("ButtonNotebook.close", {"side": "left", "sticky": '', "children":
                            [("ButtonNotebook.hover", {"side": "top", "sticky": ''})
                        ]})
                        ]
                        })]
                    })]
                })]
            )
        style.layout("ButtonNotebook", [("ButtonNotebook.client", {"sticky": "nswe"})])


        self.notebook = ttk.Notebook(self.root, style="ButtonNotebook")
        self.notebook.grid(row=0, column=2, sticky='nsew', columnspan=2)
        self.notebook.pressed_index = None
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # Create and configure info label
        self.info = tkinter.Label(self.root, height=1, bg="#0d1117", fg="#FFC014", anchor="w")
        self.info.grid(column=0, row=2, pady=1, sticky=('nsew'), columnspan=4)
        
        # Column and row configuration
        self.root.grid_columnconfigure(0, weight=0)  # Treeview column
        self.root.grid_columnconfigure(1, weight=0)  # Line Numbers column (if enabled)
        self.root.grid_columnconfigure(2, weight=1)  # Notebook column
        self.root.grid_columnconfigure(3, weight=0)  # Vertical Scrollbar column
        self.root.grid_rowconfigure(0, weight=1)  # Main row for TreeView and Text widget
        self.root.grid_rowconfigure(1, weight=0)  # Horizontal scrollbar row
        self.root.grid_rowconfigure(2, weight=0)  # Info label row

        # Adjust Treeview width if needed
        self.file_treeview.adjust_column_width()

    def on_tab_changed(self, event):
        selected_tab = self.notebook.select()

        # Find the filename associated with this tab in open_files
        for filename, (text_widget, tab) in open_files.items():
            if str(tab) == selected_tab:
                self.text = text_widget
                self.filepath = filename
                break
    
    def updatetitlebar(self):
        self.root.title("Goblin Mod Maker - " + self.mod.mod_name.get_text() + " - " + self.filepath)
        #self.root.update()

    def destroy_window(self):
        self.close()

    #<< Tools >>#
    def cut(self):
        self.text.event_generate("<<Cut>>")

    def copy(self):
        self.text.event_generate("<<Copy>>")

    def paste(self):
        self.text.event_generate("<<Paste>>")

    #-------------------- Searching --------------------#
    def search(self, regexp):
        """
        This method searches and highlights all instances of the given regular expression.
        Arguments: the search target as a regular expression.
        """
        self.search_regexp = regexp
        self.search_done = False
        self.remove_highlights()  # Clear previous highlights

        def perform_search(start_pos):
            """
            Searches for matches starting from start_pos and highlights them.
            """
            if self.search_done:
                return
            # Get the end of the text widget
            end_pos = self.text.index("end-1c")

            # Perform the search
            characters = tkinter.StringVar()
            index_start = self.text.search(self.search_regexp, start_pos, regexp=True, count=characters)

            if not index_start:
                # No more matches found, finish search
                if not self.search_done:
                    self.search_done = True
                    self.text.after(1000, self._check_highlights)  # Wait 500 ms before checking highlights
                return

            length = characters.get()

            # Ensure length is valid
            if int(length) <= 0:
                # Increment start_pos to avoid infinite loop and retry the search
                start_pos = f"{start_pos} + 1c"
                self.text.after(1, lambda: perform_search(start_pos))
                return

            index_end = f"{index_start}+{length}c"

            # Highlight the match
            self.text.tag_add("highlight", index_start, index_end)

            # Update start_pos to continue searching after the current match
            start_pos = index_end

            # # Ensure the search does not go beyond the end of the text widget
            # if self.text.index(start_pos) >= end_pos:
            #     # No more matches found within the bounds
            #     if not self.search_done:
            #         self.search_done = True
            #     return
            
        
            self.text.after(1000, self._check_highlights)  # Wait 500 ms before checking highlights
            # Schedule the next search iteration
            self.text.after(1, lambda: perform_search(start_pos))

        perform_search("1.0")  # Start searching from the beginning

    def _check_highlights(self):
        """
        Checks if there are any highlights and shows a prompt if so.
        """
        if self.text.tag_ranges("highlight") and not self.search_done:
            self.search_done = True
            self._show_prompt()

    def remove_highlights(self):
        if self.text.tag_ranges("highlight"):
            self.text.tag_remove("highlight", "1.0", "end")

    def _show_prompt(self):
        """
        Shows a prompt allowing the user to remove highlights.
        """
        response = messagebox.askyesno("Search Complete", "Search completed. Do you want to remove the highlights?")
        if response:
            # Remove the highlight tag
            self.text.tag_remove("highlight", "1.0", "end")
    #-------------------- Searching --------------------#

    def replace(self, regexp, subst, cp):
        """
            this method implements the search+replace compliment to the search functionality
        """
        index_start, index_end = self.search(regexp, cp)

        if index_start != index_end:
            self.text.delete(index_start, index_end)
            self.text.insert(index_start, subst)

        return index_start, index_end

    def gotoline(self, line_number):
        """
        Open a dialog to get the desired line number and navigate to it in the text widget.
        """
        
        if line_number is not None:
            # Calculate the index to jump to (line_number.0)
            index = f"{line_number}.0"
            
            # Ensure the line number is within the bounds of the text content
            max_line = int(self.text.index(tkinter.END).split('.')[0]) - 1
            if line_number > max_line:
                line_number = max_line
                index = f"{line_number}.0"
            
            # Move the cursor to the specified line
            self.text.mark_set("insert", index)
            self.text.see(index)  # Scroll the line into view
            self.text.focus()     # Ensure the text widget has focus

    def cmd(self, cmd, index_insert):
        """
            this method parses a line of text from the command line and invokes methods on the text
            as indicated for each of the implemented commands
            arguments: the command, and the insert position
        """
        index_start = ""
        index_end = ""
        regexp = ""
        linenumber = ""
        cmdchar = cmd[0:1]  # truncate newline
        cmd = cmd.strip("\n")

        if len(cmdchar) == 1:
            regexp = self.lastRegexp
            linenumber = self.markedLine

        if cmdchar == "*":
            if len(cmd) > 1:
                regexp = cmd[1:]
                index_start, index_end = self.search(regexp, index_insert)
                self.lastRegexp = regexp
        elif cmdchar == "#":
            if len(cmd) > 1:
                linenumber = cmd[1:]
            index_start, index_end = self.gotoline(linenumber)
            self.markedLine = linenumber
        elif cmdchar == "/":
            if len(cmd) > 3:  # the '/', delimter chr, 1 chr target, delimiter chr, null for minimum useful s+r
                snr = cmd[1:]
                token = snr[0]
                regexp = snr.split(token)[1]
                subst = snr.split(token)[2]
                index_start, index_end = self.replace(regexp, subst, index_insert)
        return index_start, index_end

    def cmdcleanup(self, index_start, index_end):
        """
            this method cleans up post-command and prepares the command line for re-use
            arguments: index beginning and end. ** this needs an audit, as does the entire
                                                    index start/end construct **
        """
        if index_start != "":
            self.text.mark_set("insert", index_start)
            self.text.tag_add("sel", index_start, index_end)
            # self.text.focus()
            self.text.see(index_start)
            self.cli.delete("1.0", tkinter.END)

    def cmdlaunch(self, event):
        """
            this method implements the callback for the key binding (Return Key)
            in the command line widget, wiring it up to the parser/dispatcher method.
            arguments: the tkinter event object with which the callback is associated
        """
        mods = {
            0: None,
            0x0001: 'Shift',
            0x0002: 'Caps Lock',
            0x0004: 'Control',
            0x0008: 'Left-hand Alt',
            0x0010: 'Num Lock',
            0x0080: 'Right-hand Alt',
            0x0100: 'Mouse button 1',
            0x0200: 'Mouse button 2',
            0x0400: 'Mouse button 3'
        }
        if mods[event.state] == "Shift":
            self.adjust_cli(event)
            return
        cmd = self.cli.get("1.0", tkinter.END)
        self.cli.delete("1.0", tkinter.END)
        if cmd[0] == "~":
            try:
                if cmd.count("\n") > 1:
                    exec(cmd[1:])
                else:
                    print("User Command Executed", "(" + cmd[1:-1] + ")", "Gives:", eval(cmd[1:]))
                self.root.update()
            except Exception as e:
                print(e)
        self.adjust_cli(event)
        return "break"

    def adjust_cli(self, event=None):
        height = self.cli.cget("height")
        if min(self.cli.get("1.0", tkinter.END).count("\n"), 25) != height:
            self.cli.config(height=min(self.cli.get("1.0", tkinter.END).count("\n"), 25))

    def autoindent(self, event):
        """
            this method implements the callback for the Return Key in the editor widget.
            arguments: the tkinter event object with which the callback is associated
        """
        indentation = ""
        lineindex = self.text.index("insert").split(".")[0]
        linetext = self.text.get(lineindex + ".0", lineindex + ".end")

        for character in linetext:
            if character in [" ", "\t"]:
                indentation += character
            else:
                break

        self.text.insert(self.text.index("insert"), "\n" + indentation)
        return "break"

    def tab2spaces4(self, event):
        """
            this method implements the callback for the indentation key (Tab Key) in the
            editor widget.
            arguments: the tkinter event object with which the callback is associated
        """
        self.text.insert(self.text.index("insert"), "    ")
        return "break"

    # Files and Tabs
    def loadfile(self, filename):
        """
        Load a file into a new tab in the Notebook with a close button.
        """
        try:
            if filename and filename not in open_files:
                
                # Create a new frame for the tab
                new_tab = ttk.Frame(self.notebook)

                # Create a Text widget for the file content in the new tab
                text_widget = Text(new_tab, wrap="none", **self.uiopts)
                self.text = text_widget

                # Create scrollbars for the Text widget
                xsb = Scrollbar(new_tab, orient="horizontal", command=text_widget.xview)
                ysb = Scrollbar(new_tab, orient="vertical", command=text_widget.yview)
                text_widget.configure(xscrollcommand=xsb.set, yscrollcommand=ysb.set)

                lineNums_uiopts = {
                    "height": 60,
                    "width": 5,
                    "cursor": "xterm",
                    "bg": "#2c314d",
                    "fg": "#FFAC00",
                    "insertbackground": "#FFD310",
                    "insertborderwidth": 1,
                    "insertwidth": 3,
                    "exportselection": True,
                    "undo": True,
                    "selectbackground": "#E0000E",
                    "inactiveselectbackground": "#E0E0E0"
                }

                if self.settings["Show Line Numbers"]:
                    self.lineNums = LineNumbers(new_tab, text_widget, **lineNums_uiopts)

                # Grid layout for the Text widget and scrollbars in the tab
                self.lineNums.grid(row=0, column=0, sticky='ns')
                text_widget.grid(row=0, column=1, sticky='nsew')  # Allow the Text widget to expand
                ysb.grid(row=0, column=2, sticky='ns')  # Place vertical scrollbar to the right of the Text widget
                xsb.grid(row=1, column=1, sticky='ew')  # Place horizontal scrollbar below the Text widget

                # Configure grid layout within the tab to allow resizing
                new_tab.grid_rowconfigure(0, weight=1)
                new_tab.grid_columnconfigure(1, weight=1)

                # Insert file contents into the Text widget
                with open(filename, 'r') as file:
                    contents = file.read()
                    text_widget.delete("1.0", tkinter.END)
                    text_widget.insert("1.0", contents)

                # Set the tab title and close button
                revised_name = os.path.basename(filename)

                # Pack the label and close button next to each other
                # Add the tab with the custom title (label + close button)
                self.notebook.add(new_tab, text=revised_name, compound="right", padding=5)
                # self.notebook.tab(new_tab, compound="left")
                self.notebook.select(new_tab)

                # Refresh and style the text widget
                self.refresh(updateMod=True)
                self.create_tags(text_widget)
                self.bootstrap = [partial(self.recolorize, text_widget)]
                self.recolorize(text_widget)
                
                def btn_press(event):
                    x, y, widget = event.x, event.y, event.widget
                    elem = widget.identify(x, y)
                    index = widget.index("@%d,%d" % (x, y))

                    if "close" in elem:
                        widget.state(['pressed'])  # Set pressed state if "close" is identified
                        widget.pressed_index = index
                    else:
                        widget.state(["!pressed"])  # Clear the pressed state if not the close button

                def btn_release(event):
                    x, y, widget = event.x, event.y, event.widget
                    elem = widget.identify(x, y)

                    if "close" in elem:
                        # Get the currently selected tab index
                        selected_tab = self.notebook.index("current")

                        # Remove the tab if it exists
                        if selected_tab is not None:
                            try:
                                self.notebook.forget(selected_tab)  # Forget the tab by index
                                if filename in open_files:
                                    del open_files[filename]  # Remove the file from open_files dictionary
                            except _tkinter.TclError as e:
                                print(f"Error closing tab: {e}")

                        # Generate a custom event for tab closure, if needed
                        widget.event_generate("<<NotebookClosedTab>>")

                    # Ensure the close button returns to its unpressed state
                    widget.state(["!pressed"])  # Reset the button's state after release
                    widget.pressed_index = None  # Reset the pressed index

                def btn_hover(event):
                    x, y, widget = event.x, event.y, event.widget
                    elem = widget.identify(x, y)

                    if "close" in elem:
                        widget.state(['hover'])  
                    else:
                        widget.state(['!hover'])  # Ensure hover state is cleared when not hovering

                self.root.bind_class("TNotebook", "<Motion>", btn_hover)
                self.root.bind_class("TNotebook", "<ButtonPress-1>", btn_press, True)
                self.root.bind_class("TNotebook", "<ButtonRelease-1>", btn_release)

                # Bindings for the text widget
                text_widget.bind('<Return>', self.autoindent)
                text_widget.bind('<Tab>', self.tab2spaces4)
                text_widget.bind("<KeyRelease>", self.on_key_release)
                text_widget.bind("<Button-1>", self.hide_autocomplete)
                text_widget.bind("<Tab>", self.accept_autocomplete_or_snippet)
                text_widget.bind("<space>", self.on_space_press)
                text_widget.bind("<Up>", self.on_arrow_key)
                text_widget.bind("<Down>", self.on_arrow_key)
                self.root.bind('<Control-KeyPress-z>', partial(self.undo, text_widget))
                self.root.bind('<Control-KeyPress-y>', partial(self.redo, text_widget))
                self.filepath = filename
                text_widget.edit_modified(False)
                self.scroll_data = text_widget.yview()
                text_widget.tag_configure("highlight", background="yellow")

                # Add the new tab to the Notebook with the filename as the tab title
                open_files[filename] = (text_widget, new_tab)
            elif filename in open_files:
                text_widget, existing_tab = open_files[filename]
                try:
                    self.notebook.select(existing_tab)
                    self.text = text_widget
                    
                except _tkinter.TclError:
                    print(f"Tab for {filename} is not available for selection.")
        except UnicodeDecodeError:
            messagebox.showerror("File Error", f"Unable to read the file '{filename}' due to unsupported characters.")
    
    
    # Inputs
    def event_key(self, event):
        """
            this method traps the keyboard events. anything that needs doing when a key is pressed is done here.
            arguments: the associated event object
        """
        keycode = event.keycode
        char = event.char
        self.recolorize(self.text)
        self.updatetitlebar()

        with open(self.filepath, "r") as f:
            file_content = f.read()

        text = self.text.get("1.0", "end-1c") 
        filename = os.path.basename(self.filepath)
        if text == file_content:
            self.modified = False 
            self.notebook.tab(self.notebook.select(), text=filename) 
        else:
            self.modified = True 
            self.notebook.tab(self.notebook.select(), text=f"{filename} *")

    def event_write(self, event):
        """
            the callback method for the root window 'ctrl+w' event (write the file to disk)
            arguments: the associated event object.
        """
        with open(self.filepath, "w") as filedescriptor:
            filedescriptor.write(self.text.get("1.0", tkinter.END)[:-1])

        self.text.edit_modified(False)
        self.root.title("Pyro: File Written.")

    def event_mouse(self, event):
        """
            this method traps the mouse events. anything that needs doing when a mouse
            operation occurs is done here.
            arguments: the associated event object
        """
        self.updatetitlebar()
        # self.recolorize()

    def close(self, event=None):
        self.mod.autosave(False)
        import GraphicalInterface
        GraphicalInterface.set_window_count(GraphicalInterface.get_window_count() - 1)
        self.root.destroy()
        global open_files
        open_files = {}
        if get_window_count() <= 0:
            GraphicalInterface.set_window_count(0)
            InterfaceMenu()
    
    def starting(self):
        """
            the classical tkinter event driver loop invocation, after running through any
            startup tasks
        """
        try:
            for task in self.bootstrap:
                task()
        except:
            self.bootstrap = []

    def create_tags(self, text_widget):
        """
        Creates the necessary tags for syntax highlighting in the given Text widget.
        """
        bold_font = font.Font(text_widget, text_widget.cget("font"))
        bold_font.configure(weight=font.BOLD)
        italic_font = font.Font(text_widget, text_widget.cget("font"))
        italic_font.configure(slant=font.ITALIC)
        bold_italic_font = font.Font(text_widget, text_widget.cget("font"))
        bold_italic_font.configure(weight=font.BOLD, slant=font.ITALIC)

        style = get_style_by_name('default')

        for ttype, ndef in style:
            tag_font = None

            if ndef['bold'] and ndef['italic']:
                tag_font = bold_italic_font
            elif ndef['bold']:
                tag_font = bold_font
            elif ndef['italic']:
                tag_font = italic_font

            foreground = "#%s" % ndef['color'] if ndef['color'] else None

            text_widget.tag_configure(str(ttype), foreground=foreground, font=tag_font)

    def recolorize(self, text_widget):
        """
        Recolorizes the syntax in the given Text widget based on token types.
        """
        code = text_widget.get("1.0", "end-1c")
        tokensource = self.lexer.get_tokens(code)
        start_line = 1
        start_index = 0
        end_line = 1
        end_index = 0

        for ttype, value in tokensource:
            if "\n" in value:
                end_line += value.count("\n")
                end_index = len(value.rsplit("\n", 1)[1])
            else:
                end_index += len(value)

            if value not in (" ", "\n"):
                index1 = "%s.%s" % (start_line, start_index)
                index2 = "%s.%s" % (end_line, end_index)

                for tagname in text_widget.tag_names(index1):
                    text_widget.tag_remove(tagname, index1, index2)

                text_widget.tag_add(str(ttype), index1, index2)

            start_line = end_line
            start_index = end_index

    def update_info(self):
        cursor = self.text.index(tkinter.INSERT)
        self.info['text'] = "Cursor Position: row {}, column {}".format(cursor.split(".")[0],cursor.split(".")[1])

    def get_open_files(self):
        return open_files


def add_window(window):
    global windows
    windows.append(window)


def mainloop():
    global pyros
    global windows
    while True:
        global RECENT
        if RECENT is not None:
            RECENT.root.deiconify()
            RECENT.root.update()
            RECENT.root.lift()
            try:
                RECENT.text.focus()
            except:
                global core_ui
                if core_ui.filepath and os.path.isfile(core_ui.filepath):
                    core_ui.loadfile(core_ui.filepath)
                try: 
                    RECENT.text.focus()
                except:
                    pass

            RECENT = None
        count = 0
        for pyro in pyros:
            try:
                pyro.root.state()
                exists = True
                if exists:
                    count += 1
                    if pyro.settings["Show Line Numbers"]:
                        try:
                            pyro.lineNums.match_up()
                        except AttributeError:
                            pass
                    pyro.update_info()
                    pyro.root.update()
                    #pyro.adjust_cli()
                    box = pyro.text.get("1.0", tkinter.END)[:-1]
                    modtext = pyro.mod.get_text()
                    if box != modtext:
                        pyro.refresh()
            except Exception as e:
                pass

        for window in windows:
            try:
                window.state()
                window.update()
                count += 1
            except Exception:
                pass
        for window in get_windows():
            try:
                window.state()
                window.update()
                count += 1
            except Exception:
                pass
        if count == 0:
            print("Exiting: All Windows Deleted")
            return

