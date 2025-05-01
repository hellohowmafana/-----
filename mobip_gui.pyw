import tkinter as tk
from tkinter import filedialog, messagebox
import json
import subprocess
import os
import shlex

# Configuration file path
config_file = "config.json"

# Default values
default_config = {
    "ebook_convert": r"Calibre\ebook-convert.exe",
    "mobis_files": "ebook.mobi",
    "mobis_folder": "ebooks"
}

# Load configuration
def load_config():
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default_config

# Save configuration
def save_config(config):
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

# Resolve relative paths to absolute paths
def resolve_path(path):
    return os.path.abspath(path) if not os.path.isabs(path) else path

# Run the mobip.py script
def run_script():
    config["ebook_convert"] = resolve_path(ebook_convert_var.get())
    config["mobis_files"] = " ".join([f'"{resolve_path(path)}"' for path in shlex.split(mobis_files_var.get())])
    config["mobis_folder"] = resolve_path(mobis_folder_var.get())
    save_config(config)

    try:
        # Combine files and folder paths
        mobis_paths = shlex.split(config["mobis_files"]) + [config["mobis_folder"]]

        subprocess.run([
            "python", "mobip.py",
            "--ebook_convert", config["ebook_convert"],
            *mobis_paths
        ], check=True)
        messagebox.showinfo("Success", "Processing completed successfully!")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# Browse for ebook-convert
def browse_ebook_convert():
    initial_dir = os.path.dirname(ebook_convert_var.get()) if os.path.exists(ebook_convert_var.get()) else "."
    path = filedialog.askopenfilename(title="Select ebook-convert Executable", initialdir=initial_dir)
    if path:
        ebook_convert_var.set(resolve_path(path))

# Browse for MOBI files
def browse_mobi_files():
    initial_dir = shlex.split(mobis_files_var.get())[0] if mobis_files_var.get() else "."  # Navigate to the first file if it exists
    files = filedialog.askopenfilenames(
        title="Select MOBI Files",
        filetypes=[("MOBI Files", "*.mobi")],
        initialdir=os.path.dirname(initial_dir) if os.path.exists(initial_dir) else "."
    )
    if files:
        current_files = [resolve_path(file) for file in files]  # Resolve paths
        mobis_files_var.set(" ".join([f'"{path}"' for path in current_files]))
        config["mobis_files"] = mobis_files_var.get()
        save_config(config)

# Browse for a folder
def browse_mobi_folder():
    initial_dir = shlex.split(mobis_folder_var.get())[0] if mobis_folder_var.get() else "."  # Navigate to the first folder if it exists
    folder = filedialog.askdirectory(
        title="Select a Folder Containing MOBI Files",
        initialdir=initial_dir if os.path.exists(initial_dir) else "."
    )
    if folder:
        mobis_folder_var.set(resolve_path(folder))  # Resolve path
        config["mobis_folder"] = mobis_folder_var.get()
        save_config(config)

# Load configuration
config = load_config()

# Create GUI
root = tk.Tk()
root.title("MOBI Processor")

# Center the window on the screen
def center_window(window):
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    window_width = window.winfo_width()
    window_height = window.winfo_height()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    window.geometry(f"+{x}+{y}")

# ebook-convert path
tk.Label(root, text="ebook-convert:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
ebook_convert_var = tk.StringVar(value=config["ebook_convert"])
tk.Entry(root, textvariable=ebook_convert_var, width=50).grid(row=0, column=1, padx=5, pady=5)
tk.Button(root, text="Browse", command=browse_ebook_convert).grid(row=0, column=2, padx=5, pady=5)

# MOBI files
tk.Label(root, text="MOBI Files:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
mobis_files_var = tk.StringVar(value=config["mobis_files"])
tk.Entry(root, textvariable=mobis_files_var, width=50).grid(row=1, column=1, padx=5, pady=5)
tk.Button(root, text="Browse Files", command=browse_mobi_files).grid(row=1, column=2, padx=5, pady=5)

# MOBI folder
tk.Label(root, text="MOBI Folder:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
mobis_folder_var = tk.StringVar(value=config["mobis_folder"])
tk.Entry(root, textvariable=mobis_folder_var, width=50).grid(row=2, column=1, padx=5, pady=5)
tk.Button(root, text="Browse Folder", command=browse_mobi_folder).grid(row=2, column=2, padx=5, pady=5)

# Run button
tk.Button(root, text="Run", command=run_script, bg="green", fg="white").grid(row=3, column=1, pady=10)

# Center the window after all components are added
root.update_idletasks()  # Ensure all widgets are rendered
root.geometry(f"{root.winfo_width()}x{root.winfo_height()}")  # Set initial size
center_window(root)

root.mainloop()
