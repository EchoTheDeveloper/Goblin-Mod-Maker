# This module is created completely by hippolippo to have a prompt in the style of pyro
import threading
from tkinter import *
from functools import partial
from pygame import mixer
from tkinter import messagebox
import json

mixer.init()

def load_theme(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return data

def load_settings():
    with open("settings.json", 'r') as file:
        data = json.load(file)
    return data

def apply_theme(root):
    global PyroPrompt_Background, PyroPrompt_Foreground, PyroPrompt_WarningTextColor
    global Click, Hover
    settings = load_settings()
    theme_data = load_theme('resources/themes/' + settings.get("Selected Theme", "Isle Goblin") + ".json")
    PyroPrompt_Background = theme_data.get("pyroprompt", {}).get("background", "")
    PyroPrompt_Foreground = theme_data.get("pyroprompt", {}).get("foreground", "")
    PyroPrompt_WarningTextColor = theme_data.get("pyroprompt", {}).get("warningtextcolor", "")

    Click = theme_data.get("click", "")
    Hover = theme_data.get("hover", "")
    
    # Apply the theme to the root window and widgets
    root.configure(background=PyroPrompt_Background)
    for widget in root.winfo_children():
        apply_theme_to_widget(widget)

def apply_theme_to_widget(widget):
    widget.configure(bg=PyroPrompt_Background, fg=PyroPrompt_Foreground)
    if isinstance(widget, Frame):
        for child in widget.winfo_children():
            apply_theme_to_widget(child)
    elif isinstance(widget, Label) or isinstance(widget, Entry):
        widget.configure(background=PyroPrompt_Background, foreground=PyroPrompt_Foreground)

def create_prompt(title, questions, fallback, cancel_fallback, defaults=None, warning=None, width=None):
    root = Tk()
    apply_theme(root)  # Apply the theme before creating the prompt
    root.title(title)
    root.resizable(0, 0)
    root.iconbitmap("resources/goblin-mod-maker.ico")
    Frame(root, width=400 if width is None else width, background=PyroPrompt_Background).pack()
    frame = Frame(root, width=400 if width is None else width, background=PyroPrompt_Background)
    frame.pack(fill="x")
    heading = Label(frame, text=title, font=("Calibri", 18), background=PyroPrompt_Background, fg=PyroPrompt_Foreground)
    heading.pack(fill="x")
    if warning is None:
        error = Label(frame, background=PyroPrompt_Background, fg=PyroPrompt_WarningTextColor)
    else:
        error = Label(frame, text=warning, background=PyroPrompt_Background, fg=PyroPrompt_WarningTextColor)
    error.pack()
    
    answers = []
    labels = []
    undo_stacks = []  # List to hold undo stacks for each Entry widget
    active_entry = [None]  # Track the currently active entry (use a list to make it mutable in nested functions)

    for question in enumerate(questions):
        labels.append(Label(frame, text=question[1], font=("Calibri", 12), background=PyroPrompt_Background, fg=PyroPrompt_Foreground))
        labels[-1].pack(fill="x")
        entry = Entry(frame, background=PyroPrompt_Background, fg=PyroPrompt_Foreground, font=("Calibri", 12))
        entry.pack(fill="x", padx=10)
        answers.append(entry)

        undo_stacks.append([""])  # Initialize the undo stack for each entry with an empty string

        entry.bind("<KeyRelease>", lambda event, e=entry, stack=undo_stacks[-1]: save_entry(e, stack))  # Bind key release to save state
        entry.bind("<FocusIn>", lambda event, e=entry: set_active_entry(e, active_entry))  # Track the currently focused entry

        if defaults is not None and question[1] in defaults:
            entry.insert(0, defaults[question[1]])

        Frame(frame, background=PyroPrompt_Background).pack(pady=10)

    # Bind Ctrl+Z for undo in the root window
    root.bind_all("<Control-z>", lambda event: undo_entry(active_entry[0], undo_stacks[answers.index(active_entry[0])] if active_entry[0] in answers else None))

    buttons = Frame(root, background=PyroPrompt_Background)
    buttons.pack()
    Button(buttons, text="Cancel", bg=PyroPrompt_Background, fg=PyroPrompt_Foreground, command=partial(cancel, root, cancel_fallback)).grid(row=0, column=0, padx=10, pady=(10, 10))
    Button(buttons, text="Done", bg=PyroPrompt_Background, fg=PyroPrompt_Foreground, command=partial(done, root, fallback, answers, error)).grid(row=0, column=1, padx=10, pady=(10, 10))
    
    return labels

def save_entry(entry, undo_stack):
    # Save the current state of the entry widget to the undo stack
    current_text = entry.get()
    if len(undo_stack) == 0 or undo_stack[-1] != current_text:
        undo_stack.append(current_text)

def undo_entry(entry, undo_stack):
    # Undo the last change for the focused Entry widget
    if entry is not None and undo_stack is not None and len(undo_stack) > 1:
        undo_stack.pop()  # Remove the current state
        previous_text = undo_stack[-1]  # Get the previous state
        entry.delete(0, END)  # Clear the entry
        entry.insert(0, previous_text)  # Insert the previous state

def set_active_entry(entry, active_entry):
    # Set the currently focused entry
    active_entry[0] = entry


def create_int_prompt(title, question, fallback, cancel_fallback, default=None, warning=None, min_value=None, width=None):
    root = Tk()
    apply_theme(root)  # Apply the theme before creating the prompt
    root.title(title)
    root.resizable(0, 0)
    root.iconbitmap("resources/goblin-mod-maker.ico")
    Frame(root, width=400 if width is None else width, background=PyroPrompt_Background).pack()
    frame = Frame(root, width=400 if width is None else width, background=PyroPrompt_Background)
    frame.pack(fill="x")
    heading = Label(frame, text=title, font=("Calibri", 18), background=PyroPrompt_Background, fg=PyroPrompt_Foreground)
    heading.pack(fill="x")
    if warning is None:
        error = Label(frame, background=PyroPrompt_Background, fg=PyroPrompt_WarningTextColor)
    else:
        error = Label(frame, text=warning, background=PyroPrompt_Background, fg=PyroPrompt_WarningTextColor)
    error.pack()
    label = Label(frame, text=question, font=("Calibri", 12), background=PyroPrompt_Background, fg=PyroPrompt_Foreground)
    label.pack(fill="x")

    answer = Spinbox(frame, background=PyroPrompt_Background, from_=1, to=99999, increment=1, fg=PyroPrompt_Foreground, font=("Calibri", 12))
    answer.pack(fill="x", padx=10)

    undo_stack = [default]  # Initialize the undo stack with the default value
    last_action = ["typing"]  # Track the last action type
    last_value = [default]  # Track the last value

    answer.bind("<KeyRelease>", lambda event: save_spinbox(answer, undo_stack, last_action, last_value))  # Save state on key release
    answer.bind("<FocusIn>", lambda event: last_value.__setitem__(0, answer.get()))  # Update last_value on focus
    answer.bind("<ButtonRelease>", lambda event: handle_spinbox_change(answer, last_action, last_value))  # Handle spinbox changes

    if default is not None:
        answer.insert(0, default)

    Frame(frame, background=PyroPrompt_Background).pack(pady=10)
    buttons = Frame(root, background=PyroPrompt_Background)
    buttons.pack()
    Button(buttons, text="Cancel", bg=PyroPrompt_Background, fg=PyroPrompt_Foreground, command=partial(cancel, root, cancel_fallback)).grid(row=0, column=0, padx=10, pady=(10, 10))
    Button(buttons, text="Done", bg=PyroPrompt_Background, fg=PyroPrompt_Foreground, command=partial(done_int, root, fallback, answer, error, min_value)).grid(row=0, column=1, padx=10, pady=(10, 10))

    root.bind_all("<Control-z>", lambda event: undo_spinbox(answer, undo_stack, last_action, last_value))

def save_spinbox(spinbox, undo_stack, last_action, last_value):
    current_value = spinbox.get()
    if len(undo_stack) == 0 or undo_stack[-1] != current_value:
        undo_stack.append(current_value)
    last_value[0] = current_value  # Always update last_value to current

def handle_spinbox_change(spinbox, last_action, last_value):
    last_action[0] = "click"  # Mark the last action as a click
    last_value[0] = spinbox.get()  # Update last value to the current Spinbox value

def undo_spinbox(spinbox, undo_stack, last_action, last_value):
    if spinbox is not None and undo_stack is not None and len(undo_stack) > 1:
        if last_action[0] == "click":
            # If the last action was a click, decrement the Spinbox value
            try:
                current_value = int(spinbox.get())
                new_value = max(1, current_value - 1)  # Ensure it doesn't go below 1
                spinbox.delete(0, END)
                spinbox.insert(0, new_value)
                undo_stack.append(str(new_value))  # Push new value to undo stack
            except ValueError:
                pass
        else:
            #!!! CURRENTLY DOESN'T WORK !!!
            undo_stack.pop()  # Remove the current state
            previous_value = undo_stack[-1]  # Get the previous state
            spinbox.delete(0, END)  # Clear the Spinbox
            spinbox.insert(0, previous_value)  # Insert the previous state
            last_value[0] = previous_value


def cancel(root, fallback):
    try:
            mixer.music.load(Click)
            mixer.music.play(loops=0)
    except:
        pass
    root.destroy()
    if fallback is None:
        return
    fallback(None)

def done(root, fallback, answers, error):
    try:
        mixer.music.load(Click)
        mixer.music.play(loops=0)
    except:
        pass
    try:
        x = fallback([i.get() for i in answers])
    except TypeError:
        x = fallback([i.get() for i in answers], root)
    if x is not None:
        error.configure(text=x)
        root.focus()
    else:
        cancel(root, None)
    try:    
        apply_theme(root)  # Reload the theme after prompt completion
    except:
        pass

def done_int(root, fallback, answer, error, min_value):
    try:
        mixer.music.load(Click)
        mixer.music.play(loops=0)
    except:
        pass
    try:
        value = int(answer.get())
        if min_value is not None and value < min_value:
            error.configure(text=f"Value must be at least {min_value}.")
            root.focus()
            return
    except ValueError:
        error.configure(text="Please enter a valid integer.")
        root.focus()
        return

    x = fallback(value)
    if x is not None:
        error.configure(text=x)
        root.focus()
    else:
        cancel(root, None)
    apply_theme(root)  # Reload the theme after prompt completion

if __name__ == "__main__":
    def x(x):
        return "hi"
    create_prompt("Test Prompt", ("Question 1", "Question 2", "Question 3"), x, print)
