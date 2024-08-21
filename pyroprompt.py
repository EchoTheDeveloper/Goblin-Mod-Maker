# This module is created completely by hippolippo to have a prompt in the style of pyro
import threading
from tkinter import *
from functools import partial
from tkinter import messagebox
import json

def load_theme(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return data

theme_data = load_theme('resources/theme.json')

PyroPrompt_Background = theme_data.get("pyroprompt_background", "")
PyroPrompt_Foreground = theme_data.get("pyroprompt_foreground", "")
PyroPrompt_WarningTextColor = theme_data.get("pyroprompt_warningtextcolor", "")

def create_prompt(title, questions, fallback, cancel_fallback, defaults=None, warning=None, width=None):
    root = Tk()
    root.configure(background=PyroPrompt_Background)
    root.title(title)
    root.resizable(0, 0)
    root.iconbitmap("resources/isle-goblin-mod-maker.ico")
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
    for question in enumerate(questions):
        labels.append(Label(frame, text=question[1], font=("Calibri", 12), background=PyroPrompt_Background, fg=PyroPrompt_Foreground))
        labels[-1].pack(fill="x")
        answers.append(Entry(frame, background=PyroPrompt_Background, fg=PyroPrompt_Foreground, font=("Calibri", 12)))
        answers[-1].pack(fill="x", padx=10)
        if defaults is not None and question[1] in defaults:
            answers[-1].insert(0, defaults[question[1]])
        Frame(frame, background=PyroPrompt_Background).pack(pady=10)
    buttons = Frame(root, background=PyroPrompt_Background)
    buttons.pack()
    Button(buttons, text="Cancel", bg=PyroPrompt_Background, fg=PyroPrompt_Foreground, command=partial(cancel, root, cancel_fallback)).grid(row=0, column=0, padx=10, pady=(10, 10))
    Button(buttons, text="Done", bg=PyroPrompt_Background, fg=PyroPrompt_Foreground, command=partial(done, root, fallback, answers, error)).grid(row=0, column=1, padx=10, pady=(10, 10))
    return labels

def create_int_prompt(title, question, fallback, cancel_fallback, default=None, warning=None, min_value=None, width=None):
    root = Tk()
    root.configure(background=PyroPrompt_Background)
    root.title(title)
    root.resizable(0, 0)
    root.iconbitmap("resources/isle-goblin-mod-maker.ico")
    Frame(root, width=400 if width is None else width, background=PyroPrompt_Background).pack()
    frame = Frame(root, width=400 if width is None else width, background="PyroPrompt_Background")
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
    answer = Entry(frame, background=PyroPrompt_Background, fg=PyroPrompt_Foreground, font=("Calibri", 12))
    answer.pack(fill="x", padx=10)
    if default is not None:
        answer.insert(0, default)
    Frame(frame, background=PyroPrompt_Background).pack(pady=10)
    buttons = Frame(root, background=PyroPrompt_Background)
    buttons.pack()
    Button(buttons, text="Cancel", bg=PyroPrompt_Background, fg=PyroPrompt_Foreground, command=partial(cancel, root, cancel_fallback)).grid(row=0, column=0, padx=10, pady=(10, 10))
    Button(buttons, text="Done", bg=PyroPrompt_Background, fg=PyroPrompt_Foreground, command=partial(done_int, root, fallback, answer, error, min_value)).grid(row=0, column=1, padx=10, pady=(10, 10))

def cancel(root, fallback):
    root.destroy()
    if fallback is None:
        return
    fallback(None)

def done(root, fallback, answers, error):
    try:
        x = fallback([i.get() for i in answers])
    except TypeError:
        x = fallback([i.get() for i in answers], root)
    if x is not None:
        error.configure(text=x)
        root.focus()
    else:
        cancel(root, None)

def done_int(root, fallback, answer, error, min_value):
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


if __name__ == "__main__":
    def x(x):
        return "hi"
    create_prompt("Test Prompt", ("Question 1", "Question 2", "Question 3"), x, print)
