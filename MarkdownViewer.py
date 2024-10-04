import os
import re
import json
import pyro
import webbrowser

from GraphicalInterface import *  # Ensure this module is present and correctly implemented.
from tkinter import Tk, ttk
from tkinterweb import HtmlFrame
import markdown
import requests



def load_theme(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return data


def load_settings():
    with open("settings.json", 'r') as file:
        data = json.load(file)
    return data


def refresh_theme():
    global InterfaceMenu_Background, InterfaceMenu_Geometry, InterfaceMenu_NewButtonBackground
    global InterfaceMenu_OpenButtonBackground, InterfaceMenu_MouseEnter, InterfaceMenu_MouseExit
    global InterfaceMenu_ButtonConfigFG, InterfaceMenu_ButtonConfigBG, PyroPrompt_Background
    global PyroPrompt_Foreground, PyroPrompt_WarningTextColor, PyroPrompt_Selected, Click, Hover

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


class MarkdownViewer(Tk):
    def __init__(self, markdown_url, backup_file=None):
        refresh_theme()
        super().__init__()
        self.title("GMM Documentation")
        self.geometry("1000x600")
        self.configure(bg=InterfaceMenu_Background)

        # Configure grid layout
        self.columnconfigure(0, weight=1)  # Treeview
        self.columnconfigure(1, weight=4)  # HtmlFrame
        self.rowconfigure(0, weight=1)     # Single row

        # Initialize the treeview
        self.tree = ttk.Treeview(self, selectmode='browse')
        self.tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.tree.heading("#0", text="Table of Contents", anchor="w")
        self.tree.bind("<<TreeviewSelect>>", self.on_toc_select)

        
        # Setup Treeview style
        self.setup_treeview_style()

        # Create a frame for the HtmlFrame
        html_frame_container = ttk.Frame(self)
        html_frame_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Initialize HtmlFrame inside the ttk.Frame
        self.html_frame = HtmlFrame(html_frame_container, messages_enabled=False)
        self.html_frame.on_link_click(self.handle_link_click)
        self.html_frame.pack(fill="both", expand=True)

        self.header_count = {}
        self.file = backup_file # Sets the backup file incase of emergency
        self.url = markdown_url
        # self.load_markdown()
        self._load_markdown()
        # pyro.add_window(self)
        mainloop()

    def handle_link_click(self, url):
        """Handle link clicks. If the link is internal, scroll to the appropriate section."""
        if "#" in url:  # Check if the URL contains an internal anchor
            element_id = url.split("#")[-1]  # Extract the part after the '#'
            element_id = self.create_safe_id(element_id)
            if element_id:  # Ensure the element ID is not empty
                self.html_frame.yview_toelement(f'#{element_id}')  # Scroll to the element with the given id
            else:
                print(f"Ignoring invalid anchor in URL: {url}")
        elif url.startswith("http"):  # External links
            webbrowser.open(url)  # Open in the default browser
        else:
            print(f"Ignoring invalid URL: {url}")

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

        # Apply this style to the treeview
        self.tree.configure(style="Treeview")
        
        self.tree.tag_configure('row', background=InterfaceMenu_MouseEnter, foreground=PyroPrompt_Foreground)
        
        style.configure("Treeview.Column",
                        background=PyroPrompt_Background,  # Background for headers
                        foreground=PyroPrompt_Foreground,  # Header text color
                        bordercolor=InterfaceMenu_MouseEnter,
                        relief="flat")

    def load_markdown(self):
        # self.after(0, self._load_markdown)
        self._load_markdown()

    def _load_markdown(self):
        markdown_content = self.read_markdown_file(url=self.url, file=self.file)
        html_content = self.convert_markdown_to_html(markdown_content)
        self.html_frame.load_html(html_content)
        self.generate_toc(markdown_content)

    def read_markdown_file(self, url=None, file=None):
        if url:
            try:
                response = requests.get(url)
                response.raise_for_status()  # Checks for errors
                return response.text
            except requests.RequestException as e:
                print(f"Error fetching markdown from URL: {e}")
                # Optionally fallback to file
        if file:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    return f.read()
            except FileNotFoundError:
                print(f"File not found: {file}")

        
    def convert_markdown_to_html(self, markdown_content):
        modified_content = self.add_ids_to_headers(markdown_content)
        # Resolve image paths to absolute paths before converting to HTML
        modified_content = self.resolve_image_paths(modified_content)
        return markdown.markdown(modified_content, extensions=['tables'])

    def resolve_image_paths(self, markdown_content):
        # This will only modify local image paths, keeping URLs intact
        if not self.file:
            return markdown_content  # If no file, no need to modify paths
        
        markdown_dir = os.path.dirname(os.path.abspath(self.file)) if self.file else os.getcwd()
        
        def replace_image_paths(match):
            image_path = match.group(2)
            # Modify only if it's not an external URL
            if not image_path.startswith("http"):
                absolute_path = os.path.join(markdown_dir, image_path)
                normalized_path = os.path.normpath(absolute_path)
                file_url = 'file:///' + normalized_path.replace(os.path.sep, '/')
                return f'![{match.group(1)}]({file_url})'
            return match.group(0)  # Leave web URLs unchanged

        return re.sub(r'!\[(.*?)\]\((.*?)\)', replace_image_paths, markdown_content)

    def add_ids_to_headers(self, markdown_content):
        def add_id(match):
            level = len(match.group(1))
            header_text = match.group(2).strip()
            safe_id = self.create_safe_id(header_text)
            return f'<h{level} id="{safe_id}" style="color: #333;">{header_text}</h{level}>'
        return re.sub(r'^(#{1,6})\s+(.+)', add_id, markdown_content, flags=re.MULTILINE)

    def create_safe_id(self, header_text):
        return re.sub(r'[\s\'.,]+', '-', re.sub(r'[\\/:]', '', header_text.lower()))

    def generate_toc(self, markdown_content):
        headers = re.findall(r'^(#{1,6})\s+(.+)', markdown_content, re.MULTILINE)
        parent_stack = []

        for header in headers:
            level, text = len(header[0]), header[1].strip()
            safe_id = self.make_unique_id(text)

            while len(parent_stack) >= level:
                parent_stack.pop()

            current_parent = self.tree.insert(parent_stack[-1] if parent_stack else "", "end", text=text, iid=safe_id)
            parent_stack.append(safe_id)

        # Expand the first item in the TOC
        if self.tree.get_children():
            self.tree.item(self.tree.get_children()[0], open=True)
        
        self.setup_treeview_style()


    def make_unique_id(self, text):
        safe_id = self.create_safe_id(text)
        if safe_id in self.header_count:
            self.header_count[safe_id] += 1
            return f"{safe_id}-{self.header_count[safe_id]}"
        else:
            self.header_count[safe_id] = 1
            return safe_id

    def on_toc_select(self, event):
        selected_item = self.tree.selection()
        if selected_item:
            self.html_frame.yview_toelement(f'#{selected_item[0]}')
            print(selected_item[0])

# Commented this because everytime i open the app this pops up
# markdown_file = "https://raw.githubusercontent.com/EchoTheDeveloper/Goblin-Mod-Maker/refs/heads/main/DOCUMENTATION.md"
# MarkdownViewer(markdown_file, "DOCUMENTATION.md")
