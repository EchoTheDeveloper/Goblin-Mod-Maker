#!/usr/bin/env python


"""
    UnityModderPyro, Modified to work for Unity Mod Maker By Hippolippo

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

pyros = []
windows = []

class LineNumbers(Text): #scrolledtext.ScrolledText
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
        final_index = str(self.text.index(tkinter.END))
        temp = self.num_of_lines
        self.num_of_lines = final_index.split('.')[0]
        line_numbers_string = "\n".join(str(1 + no) for no in range(int(self.num_of_lines)))
        width = len(str(self.num_of_lines)) + 3

        self.configure(state='normal', width=width)
        if self.num_of_lines != temp:
            self.delete(1.0, tkinter.END)
            self.insert(1.0, line_numbers_string)
        self.configure(state='disabled')
        self.scroll_data = self.text.yview()
        self.yview_moveto(self.scroll_data[0])


class CoreUI(object):
    """
        CoreUI is the editor object, derived from class 'object'. It's instantiation initilizer requires the
        ubiquitous declaration of the 'self' reference implied at call time, as well as a handle to
        the lexer to be used for text decoration.
    """

    def __init__(self, lexer, filename="Untitled", mod=None, settings={}):
        global RECENT
        RECENT = self
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
        self.root.iconbitmap("resources/isle-goblin-mod-maker.ico")
        self.root.protocol("WM_DELETE_WINDOW", self.destroy_window)
        self.uiconfig()
        self.root.bind("<Key>", self.event_key)
        self.root.bind('<Control-KeyPress-q>', self.close)
        self.root.bind('<Control-KeyPress-z>', self.undo)
        self.root.bind('<Control-KeyPress-y>', self.redo)
        # self.root.bind('<Control-KeyPress-f>', MenuMethods.openSearch(self)) DOESNT WORK CURRENTLY
        self.root.bind('<Button>', self.event_mouse)
        self.root.bind('<Configure>', self.event_mouse)
        self.text.bind('<Return>', self.autoindent)
        self.text.bind('<Tab>', self.tab2spaces4)
        self.create_tags()
        self.text.edit_modified(False)
        self.bootstrap = [self.recolorize]
        self.loadfile(self.contents)
        self.recolorize()
        self.root.geometry("1200x700+10+10")
        self.initialize_menubar()
        self.updatetitlebar()
        self.scroll_data = self.text.yview()
        self.starting()
        global pyros
        pyros.append(self)
        self.text.tag_configure("highlight", background="yellow")
        self.search_done = False
        self.search_regexp = None

        def load_file(filename):
            with open(filename, 'r') as file:
                data = json.load(file)
            return data

        self.keywords = load_file("resources/keywords.json")

        # Define snippets
        self.snippets = load_file("resources/snippets.json")

        self.text.bind("<KeyRelease>", self.on_key_release)
        self.text.bind("<Button-1>", self.hide_autocomplete)
        self.text.bind("<Tab>", self.accept_autocomplete_or_snippet)
        self.text.bind("<space>", self.on_space_press)
        self.text.bind("<Up>", self.on_arrow_key)
        self.text.bind("<Down>", self.on_arrow_key)

        self.autocomplete_window = None

    def undo(self, e=None):
        mod = ChangeManager.undo()
        if mod is not None:
            self.mod = mod
            self.refresh(False)
        return "break"

    def redo(self, e):
        mod = ChangeManager.redo()
        if mod is not None:
            self.mod = mod
            self.refresh(False)
        return "break"

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

        self.filemenu.add_command(label="New", command=partial(MenuMethods.new,self.settings))
        self.filemenu.add_command(label="Open", command=partial(MenuMethods.open, self.settings))
        self.filemenu.add_command(label="Save", command=partial(MenuMethods.save, self, self.filename))
        self.filemenu.add_command(label="Save as Renamed Copy", command=partial(MenuMethods.copy, self))
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Close", command=self.close)



        self.menubar.add_cascade(label="Edit", menu=self.editmenu)

        self.editmenu.add_command(label="Change Mod Name", command=partial(MenuMethods.change_mod_name, self))
        self.editmenu.add_command(label="Change Mod Version",command=partial(MenuMethods.change_mod_version, self))
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



        self.menubar.add_cascade(label="Build", menu=self.buildmenu)

        self.buildmenu.add_command(label="Build and Install", command=partial(MenuMethods.build_install, self))
        self.buildmenu.add_command(label="Export C# File", command=partial(MenuMethods.export_cs, self))
        self.buildmenu.add_command(label="Generate Dotnet Files", command=partial(MenuMethods.export_dotnet, self))


        self.menubar.add_cascade(label="Tools", menu=self.toolsmenu)

        self.toolsmenu.add_command(label="Search", command=partial(MenuMethods.openSearch, self))
        # self.toolsmenu.add_command(label="Search and Replace", command=self.replace)
        self.toolsmenu.add_command(label="Go To Line", command=partial(MenuMethods.openGTL, self))


        self.menubar.add_cascade(label="Snippets", command=self.snippetsmenu)

        # self.toolsmenu.add_command(label="Public Void", command=inject_line(self, codeToInject="private"))
        self.snippetsmenu.add_command(label="Go To Line", command=partial(MenuMethods.openGTL, self))


        # self.menubar.add_command(label="Remove Highlights", command=self.remove_highlights)

        self.root.config(menu=self.menubar)

    #-------------------- Autocomplete and Snippets --------------------#
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
            self.root.bind("<Button-1>", self.on_click_outside)

    def insert_autocomplete(self):
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
        line_text = self.text.get(f"{cursor_position} linestart", cursor_position)
        current_word = line_text.split()[-1] if line_text.split() else ""

        # Check if the current word matches a snippet trigger
        if current_word in self.snippets and current_word not in self.keywords:
            self.text.insert(INSERT, self.snippets[current_word])
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
    #-------------------- Autocomplete and Snippets --------------------#

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
        self.text.delete("1.0", tkinter.END)
        self.text.insert("1.0", self.mod.get_text())
        self.recolorize()
        if self.mod.get_text() == text and text is not None:
            self.text.mark_set("insert", str(cursor))
        else:
            text = self.text.get("1.0", tkinter.END).split("\n")
            a, i = 0, 0
            while a + len(text[i]) + 1 < index and i < len(text):
                a += len(text[i])
                a += 1
                i += 1
            j = index - a
            self.text.mark_set("insert", "%d.%d" % (i + 1, j))
        # self.root.update()
        self.text.yview_moveto(self.scroll_data[0])

    def uiconfig(self):
        """
            this method sets up the main window and two text widgets (the editor widget, and a
            text entry widget for the commandline).
        """
        self.uiopts = {"height": "1000",
                       "width": "1000",
                       "cursor": "xterm",
                       "bg": "#0d1117",
                       "fg": "#FFAC00",
                       "insertbackground": "#FFD310",
                       "insertborderwidth": "1",
                       "insertwidth": "3",
                       "exportselection": True,
                       "undo": True,
                       "selectbackground": "#E0000E",
                       "inactiveselectbackground": "#E0E0E0",
                       }
        self.text = Text(master=self.root, wrap="none", **self.uiopts)
        self.xsb = Scrollbar(self.root, orient="horizontal", command=self.text.xview)
        self.text.configure(xscrollcommand=self.xsb.set)
        self.xsb.grid(row=1, column=0, columnspan=2,sticky=(E,W))
        self.ysb = Scrollbar(self.root, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=self.ysb.set)
        self.ysb.grid(row=0, column=2,sticky=(N,S), rowspan=2)
        self.ysb.configure(
            activebackground="#0d1117",
            borderwidth="0",
            background="#0d1117",
            highlightthickness="0",
            highlightcolor="#00062A",
            highlightbackground="#252c36",
            troughcolor="#20264A",
            relief="flat")
        '''self.cli = tkinter.Text(self.root, {"height": "1",
                                            "bg": "#191F44",
                                            "fg": "#FFC014",
                                            "insertbackground": "#FFD310",
                                            "insertborderwidth": "1",
                                            "insertwidth": "3",
                                            "exportselection": True,
                                            "undo": True,
                                            "selectbackground": "#E0000E",
                                            "inactiveselectbackground": "#E0E0E0"
                                            })'''
        self.info = tkinter.Label(self.root, {"height": "1",
                                            "bg": "#0d1117",
                                            "fg": "#FFC014",
                                            "anchor": "w"
                                            })
        lineNums_uiopts = {"height": "60",
                       "width": "8",
                       "cursor": "xterm",
                       "bg": "#2c314d",
                       "fg": "#FFAC00",
                       "insertbackground": "#FFD310",
                       "insertborderwidth": "1",
                       "insertwidth": "3",
                       "exportselection": True,
                       "undo": True,
                       "selectbackground": "#E0000E",
                       "inactiveselectbackground": "#E0E0E0"
                       }
        if self.settings["Show Line Numbers"] == True:
            self.lineNums = LineNumbers(self.root, self.text, **lineNums_uiopts)
            self.lineNums.grid(column=0,row=0,sticky=('nsew'))
        self.text.grid(column=1, row=0, sticky=('nsew'))
        self.root.grid_columnconfigure(0, weight=0)
        self.root.grid_columnconfigure(1, weight=1)
        self.info.grid(column=0, row=2, pady=1, sticky=('nsew'),columnspan=3)
        self.info.visible = True
        #self.cli.grid(column=0, row=1, pady=1, sticky=('nsew'))
        #self.cli.bind("<Return>", self.cmdlaunch)
        #self.cli.bind("<KeyRelease>", self.adjust_cli)
        #self.cli.visible = True
        #self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)

    def updatetitlebar(self):
        self.root.title("Isle Goblin Mod Maker - " + self.filename)
        #self.root.update()

    def destroy_window(self):
        self.close()

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

    def loadfile(self, text):
        """
            this method implements loading a file into the editor.
            arguments: the scrollable text object into which the text is to be loaded
        """
        if text:
            self.text.insert(tkinter.INSERT, text)
            self.text.tag_remove(tkinter.SEL, '1.0', tkinter.END)
            self.text.see(tkinter.INSERT)

    def event_key(self, event):
        """
            this method traps the keyboard events. anything that needs doing when a key is pressed is done here.
            arguments: the associated event object
        """
        keycode = event.keycode
        char = event.char
        self.recolorize()
        self.updatetitlebar()

    def event_write(self, event):
        """
            the callback method for the root window 'ctrl+w' event (write the file to disk)
            arguments: the associated event object.
        """
        with open(self.filename, "w") as filedescriptor:
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
        if get_window_count() <= 0:
            GraphicalInterface.set_window_count(0)
            InterfaceMenu()

    # ---------------------------------------------------------------------------------------

    def starting(self):
        """
            the classical tkinter event driver loop invocation, after running through any
            startup tasks
        """
        for task in self.bootstrap:
            task()

    def create_tags(self):
        """
            thmethod creates the tags associated with each distinct style element of the
            source code 'dressing'
        """
        bold_font = font.Font(self.text, self.text.cget("font"))
        bold_font.configure(weight=font.BOLD)
        italic_font = font.Font(self.text, self.text.cget("font"))
        italic_font.configure(slant=font.ITALIC)
        bold_italic_font = font.Font(self.text, self.text.cget("font"))
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

            if ndef['color']:
                foreground = "#%s" % ndef['color']
            else:
                foreground = None

            self.text.tag_configure(str(ttype), foreground=foreground, font=tag_font)

    def recolorize(self):
        """
            this method colors and styles the prepared tags
        """
        code = self.text.get("1.0", "end-1c")
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

                for tagname in self.text.tag_names(index1):  # FIXME
                    self.text.tag_remove(tagname, index1, index2)

                self.text.tag_add(str(ttype), index1, index2)

            start_line = end_line
            start_index = end_index

    def update_info(self):
        cursor = self.text.index(tkinter.INSERT)
        self.info['text'] = "Cursor Position: row {}, column {}".format(cursor.split(".")[0],cursor.split(".")[1])



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
            RECENT.text.focus()
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

