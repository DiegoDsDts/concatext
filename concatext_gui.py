"""
concatext_gui.py

GUI for Concatext that allows configuring and running
the file concatenation process.
"""

import os
import sys
import yaml
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, simpledialog
from pathlib import Path
import threading
import subprocess

# Import functionalities from the main module
import concatext

class TemplateEditorDialog(tk.Toplevel):
    def __init__(self, parent, template_text=""):
        super().__init__(parent)
        self.parent = parent
        self.title("File Template Editor")
        self.geometry("600x400")
        self.minsize(500, 300)
        
        # Make the dialog modal
        self.transient(parent)
        self.grab_set()
        
        self.result = None
        
        # Create widgets
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        help_text = "Use these placeholders:\n{path} - Relative file path\n{name} - File name\n{content} - File content"
        ttk.Label(main_frame, text=help_text).pack(anchor=tk.W, pady=(0, 10))
        
        # Template text area with scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.template_text = tk.Text(text_frame, wrap=tk.WORD, height=1)  # Set minimum height
        scrollbar = ttk.Scrollbar(text_frame, command=self.template_text.yview)
        self.template_text.config(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.template_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Insert initial text
        if template_text:
            self.template_text.insert("1.0", template_text)
        
        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="OK", command=self.ok_command).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_command).pack(side=tk.RIGHT, padx=5)
        
        # Focus and bind events
        self.template_text.focus_set()
        self.bind("<Return>", self.ok_command)
        self.bind("<Escape>", self.cancel_command)
        
        # Wait for window to be closed
        self.wait_window(self)
    
    def ok_command(self, event=None):
        self.result = self.template_text.get("1.0", tk.END).strip()
        self.destroy()
    
    def cancel_command(self, event=None):
        self.result = None
        self.destroy()

class SeparatorEditorDialog(tk.Toplevel):
    def __init__(self, parent, separator_text=""):
        super().__init__(parent)
        self.parent = parent
        self.title("File Separator Editor")
        self.geometry("600x300")
        self.minsize(500, 200)
        
        # Make the dialog modal
        self.transient(parent)
        self.grab_set()
        
        self.result = None
        
        # Create widgets
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        help_text = "Enter text to insert between files:\n(Use \\n for new lines)"
        ttk.Label(main_frame, text=help_text).pack(anchor=tk.W, pady=(0, 10))
        
        # Template text area with scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.separator_text = tk.Text(text_frame, wrap=tk.WORD, height=5)
        scrollbar = ttk.Scrollbar(text_frame, command=self.separator_text.yview)
        self.separator_text.config(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.separator_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Insert initial text (convert \n to visible form)
        if separator_text:
            visible_text = separator_text.replace("\n", "\\n")
            self.separator_text.insert("1.0", visible_text)
        
        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="OK", command=self.ok_command).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_command).pack(side=tk.RIGHT, padx=5)
        
        # Focus and bind events
        self.separator_text.focus_set()
        self.bind("<Return>", self.ok_command)
        self.bind("<Escape>", self.cancel_command)
        
        # Wait for window to be closed
        self.wait_window(self)
    
    def ok_command(self, event=None):
        # Get text and convert visible \n to actual newlines
        visible_text = self.separator_text.get("1.0", tk.END).strip()
        self.result = visible_text.replace("\\n", "\n")
        self.destroy()
    
    def cancel_command(self, event=None):
        self.result = None
        self.destroy()

class ListEditorDialog(tk.Toplevel):
    def __init__(self, parent, title, items=None):
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.geometry("500x400")
        self.minsize(400, 300)
        
        # Make the dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Initialize result
        self.result = items or []
        
        # Create widgets
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Input field for new items
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.new_item = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.new_item).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(input_frame, text="Add", command=self.add_item).pack(side=tk.RIGHT, padx=2)
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, height=1)  # Set minimum height
        scrollbar = ttk.Scrollbar(list_frame, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Populate listbox
        for item in self.result:
            self.listbox.insert(tk.END, item)
        
        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(action_frame, text="Remove Selected", command=self.remove_selected).pack(side=tk.LEFT, padx=2)
        
        # Bottom buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="OK", command=self.ok_command).pack(side=tk.RIGHT, padx=2)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_command).pack(side=tk.RIGHT, padx=2)
        
        # Bind events
        self.bind("<Return>", lambda e: self.add_item())
        self.bind("<Escape>", self.cancel_command)
        
        # Wait for window to be closed
        self.wait_window(self)
    
    def add_item(self):
        item = self.new_item.get().strip()
        if item:
            self.listbox.insert(tk.END, item)
            self.new_item.set("")
    
    def remove_selected(self):
        selected = self.listbox.curselection()
        if selected:
            # Remove items in reverse order to avoid index issues
            for index in sorted(selected, reverse=True):
                self.listbox.delete(index)
    
    def ok_command(self, event=None):
        # Get all items from listbox
        self.result = list(self.listbox.get(0, tk.END))
        self.destroy()
    
    def cancel_command(self, event=None):
        # Keep original items
        self.destroy()

class TextObscurationDialog(tk.Toplevel):
    def __init__(self, parent, text_map=None):
        super().__init__(parent)
        self.parent = parent
        self.title("Text Obscuration Mappings")
        self.geometry("700x500")
        self.minsize(700, 500)
        
        # Make the dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Initialize result with the provided mapping or empty dict
        self.result = text_map or {}
        
        # Create widgets
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        help_text = "Define mappings between original text and their obscured placeholders.\nEvery occurrence of the original text will be replaced with its placeholder."
        ttk.Label(main_frame, text=help_text, wraplength=600).pack(anchor=tk.W, pady=(0, 10))
        
        # Input fields for adding new mappings
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(input_frame, text="Original text:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(input_frame, text="Placeholder:").grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        self.original_text = tk.StringVar()
        self.placeholder = tk.StringVar()
        
        ttk.Entry(input_frame, textvariable=self.original_text, width=25).grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(input_frame, textvariable=self.placeholder, width=25).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(input_frame, text="Add", command=self.add_mapping).grid(row=1, column=2, padx=5, pady=5)
        
        # Table for displaying and managing mappings
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Treeview for displaying mappings
        self.tree = ttk.Treeview(table_frame, columns=("text", "placeholder"), show="headings")
        self.tree.heading("text", text="Original Text")
        self.tree.heading("placeholder", text="Placeholder")
        self.tree.column("text", width=300)
        self.tree.column("placeholder", width=300)
        
        # Scrollbar for the treeview
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate the treeview with existing mappings
        for text, placeholder in self.result.items():
            self.tree.insert("", tk.END, values=(text, placeholder))
        
        # Remove button
        ttk.Button(main_frame, text="Remove Selected", command=self.remove_selected).pack(pady=10)
        
        # Buttons frame
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="OK", command=self.ok_command).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_command).pack(side=tk.RIGHT, padx=5)
        
        # Focus and bind events
        self.original_text.trace_add("write", self.validate_inputs)
        self.placeholder.trace_add("write", self.validate_inputs)
        
        # Wait for window to be closed
        self.wait_window(self)
    
    def validate_inputs(self, *args):
        """Validate that both input fields are not empty"""
        return bool(self.original_text.get().strip() and self.placeholder.get().strip())
    
    def add_mapping(self):
        """Add a new mapping to the list"""
        text = self.original_text.get().strip()
        placeholder = self.placeholder.get().strip()
        
        if not text or not placeholder:
            messagebox.showwarning("Validation Error", "Both original text and placeholder are required.")
            return
        
        # Check if text already exists
        for item_id in self.tree.get_children():
            if self.tree.item(item_id)['values'][0] == text:
                self.tree.delete(item_id)
                break
        
        # Add to treeview
        self.tree.insert("", tk.END, values=(text, placeholder))
        
        # Clear input fields
        self.original_text.set("")
        self.placeholder.set("")
    
    def remove_selected(self):
        """Remove the selected mapping from the list"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("Selection Required", "Please select a mapping to remove.")
            return
        
        for item_id in selected_items:
            self.tree.delete(item_id)
    
    def ok_command(self, event=None):
        """Save all mappings and close dialog"""
        # Rebuild the result dictionary from the treeview
        self.result = {}
        for item_id in self.tree.get_children():
            values = self.tree.item(item_id)['values']
            text, placeholder = values
            self.result[text] = placeholder
        
        self.destroy()
    
    def cancel_command(self, event=None):
        """Cancel and close without saving changes"""
        self.result = None
        self.destroy()

class ConcatextGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Concatext")
        self.root.geometry("580x740")
        self.root.minsize(580, 600)
        
        # Configura lo stile dei pulsanti per ridurre il padding interno
        style = ttk.Style()
        style.configure('TButton', padding=(2, 0))  # Riduzione del padding orizzontale (sinistra, destra)
        
        # Variables for configurations
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.max_tokens = tk.StringVar(value="250000")
        self.include_non_text = tk.BooleanVar(value=True)
        self.non_text_placeholder = tk.StringVar(value="non-text file placeholder")
        
        # Advanced configuration data
        self.file_template = ""
        self.file_separator = "\n\n"
        self.ignore_dirs = ["node_modules", ".git", ".expo", ".vscode", "dist", "build", "tests"]
        self.ignore_patterns = [".DS_Store", ".gitignore", "package-lock.json", "*.md", "*.log"]
        self.obscured_words = {}  # Dictionary for word -> placeholder mappings
        
        # Base configuration
        self.create_widgets()
        
        # Load existing configurations, if available
        self.load_config()
    
    def create_widgets(self):
        # Main area divided into two frames
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Bind click event to remove focus from input widgets
        self.root.bind("<Button-1>", self.remove_focus)
        
        # Frame for basic configurations
        basic_config_frame = ttk.LabelFrame(main_frame, text="Basic Configuration", padding="10")
        basic_config_frame.pack(fill=tk.X, expand=False, padx=5, pady=5)
        
        # Input Directory
        input_dir_frame = ttk.Frame(basic_config_frame)
        input_dir_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(input_dir_frame, text="Input Directory:", width=20).pack(side=tk.LEFT)
        ttk.Entry(input_dir_frame, textvariable=self.input_dir).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(input_dir_frame, text="Browse...", command=self.browse_input_dir).pack(side=tk.LEFT, padx=2)
        
        # Output Directory
        output_dir_frame = ttk.Frame(basic_config_frame)
        output_dir_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(output_dir_frame, text="Output Directory:", width=20).pack(side=tk.LEFT)
        ttk.Entry(output_dir_frame, textvariable=self.output_dir).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(output_dir_frame, text="Browse...", command=self.browse_output_dir).pack(side=tk.LEFT, padx=2)
        
        # Max Tokens
        max_tokens_frame = ttk.Frame(basic_config_frame)
        max_tokens_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(max_tokens_frame, text="Max Tokens:", width=20).pack(side=tk.LEFT)
        ttk.Entry(max_tokens_frame, textvariable=self.max_tokens).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Advanced options buttons frame
        advanced_frame = ttk.Frame(basic_config_frame)
        advanced_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(advanced_frame, text="Ignore:").pack(side=tk.LEFT, padx=(0, 10))
        
        # Button container for ignore buttons with right alignment
        ignore_buttons_frame = ttk.Frame(advanced_frame)
        ignore_buttons_frame.pack(side=tk.RIGHT)
        
        # Create buttons with same width
        ttk.Button(ignore_buttons_frame, text="Files", width=8, command=self.edit_ignore_patterns).pack(side=tk.RIGHT, padx=2)
        ttk.Button(ignore_buttons_frame, text="Folders", width=8, command=self.edit_ignore_dirs).pack(side=tk.RIGHT, padx=2)
        
        # Frame for advanced configurations
        advanced_config_frame = ttk.LabelFrame(main_frame, text="Advanced Configuration", padding="10")
        advanced_config_frame.pack(fill=tk.X, expand=False, padx=5, pady=5)
        
        # File template button in a separate frame
        template_frame = ttk.Frame(advanced_config_frame)
        template_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(template_frame, text="Output structure:").pack(side=tk.LEFT, padx=(0, 10))
        
        # Button container for output structure buttons with right alignment
        template_buttons_frame = ttk.Frame(template_frame)
        template_buttons_frame.pack(side=tk.RIGHT)
        
        # Create buttons with same width
        ttk.Button(template_buttons_frame, text="Separator", width=8, command=self.edit_separator).pack(side=tk.RIGHT, padx=2)
        ttk.Button(template_buttons_frame, text="Template", width=8, command=self.edit_template).pack(side=tk.RIGHT, padx=2)
        
        # Obscured words frame
        obscured_frame = ttk.Frame(advanced_config_frame)
        obscured_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(obscured_frame, text="Obscuration:").pack(side=tk.LEFT, padx=(0, 10))
        
        # Button for obscured words settings
        obscured_buttons_frame = ttk.Frame(obscured_frame)
        obscured_buttons_frame.pack(side=tk.RIGHT)
        
        ttk.Button(obscured_buttons_frame, text="Edit", width=8, command=self.edit_text_obscuration).pack(side=tk.RIGHT, padx=2)
        
        # Non-text file options
        unsupported_frame = ttk.Frame(advanced_config_frame)
        unsupported_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.unsupported_checkbox = ttk.Checkbutton(
            unsupported_frame, 
            text="Include non-text files", 
            variable=self.include_non_text,
            command=self.toggle_non_text_message
        )
        self.unsupported_checkbox.pack(side=tk.LEFT)
        
        # Add a dedicated button frame for placeholder button
        unsupported_btn_frame = ttk.Frame(unsupported_frame)
        unsupported_btn_frame.pack(side=tk.RIGHT)
        
        self.edit_non_text_msg_button = ttk.Button(unsupported_btn_frame, text="Placeholder", width=8, command=self.edit_non_text_message)
        self.edit_non_text_msg_button.pack(side=tk.RIGHT, padx=2)
        
        # Disable the button if include_non_text is False
        if not self.include_non_text.get():
            self.edit_non_text_msg_button.configure(state='disabled')
        
        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a frame for the log area to fix the scrollbar issue
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill=tk.BOTH, expand=True)
        
        # Configure text widget for log with horizontal scrollbar and no minimum size
        self.log_area = tk.Text(log_container, wrap=tk.NONE, state='disabled', height=0, width=0)
        self.log_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Vertical scrollbar
        v_scrollbar = ttk.Scrollbar(log_container, command=self.log_area.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_area.config(yscrollcommand=v_scrollbar.set)
        
        # Horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(log_frame, orient=tk.HORIZONTAL, command=self.log_area.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.log_area.config(xscrollcommand=h_scrollbar.set)
        
        # Add a frame for the clear button at the bottom left
        log_buttons_frame = ttk.Frame(log_frame)
        log_buttons_frame.pack(side=tk.BOTTOM, fill=tk.X, before=h_scrollbar)
        
        # Add clear button at bottom left
        ttk.Button(log_buttons_frame, text="Clear", command=self.clear_log).pack(side=tk.LEFT, padx=2, pady=2)
        
        # Action buttons
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Start", command=self.run_concatext).pack(side=tk.RIGHT, padx=2)
    
    def toggle_non_text_message(self):
        """Enable or disable the placeholder button based on checkbox state"""
        if self.include_non_text.get():
            # Enable the placeholder button
            self.edit_non_text_msg_button.configure(state='normal')
        else:
            # Disable the placeholder button
            self.edit_non_text_msg_button.configure(state='disabled')
    
    def edit_template(self):
        """Open a dialog to edit the file template"""
        dialog = TemplateEditorDialog(self.root, self.file_template)
        if (dialog.result is not None):
            self.file_template = dialog.result
            self.log_message("File template updated.")
    
    def edit_separator(self):
        """Open a dialog to edit the file separator"""
        dialog = SeparatorEditorDialog(self.root, self.file_separator)
        if (dialog.result is not None):
            self.file_separator = dialog.result
            self.log_message("File separator updated.")
    
    def edit_non_text_message(self):
        """Open a dialog to edit the non-text file placeholder"""
        # Create a custom dialog for better text editing
        dialog = tk.Toplevel(self.root)
        dialog.title("non-text File Placeholder")
        dialog.geometry("600x300")
        dialog.minsize(500, 200)
        
        # Make the dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add help text
        help_text = "Enter the placeholder text to display for non-text files:"
        ttk.Label(main_frame, text=help_text).pack(anchor=tk.W, pady=(0, 10))
        
        # Text area with scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_area = tk.Text(text_frame, wrap=tk.WORD, height=10)
        scrollbar = ttk.Scrollbar(text_frame, command=text_area.yview)
        text_area.config(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Insert current message
        text_area.insert("1.0", self.non_text_placeholder.get())
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, pady=10)
        
        def ok_command():
            self.non_text_placeholder.set(text_area.get("1.0", tk.END).strip())
            self.log_message("non-text file placeholder updated.")
            dialog.destroy()
        
        ttk.Button(button_frame, text="OK", command=ok_command).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Focus and bind events
        text_area.focus_set()
        dialog.bind("<Return>", lambda e: ok_command())
        dialog.bind("<Escape>", lambda e: dialog.destroy())
        
        # Wait for window to be closed
        dialog.wait_window(dialog)
    
    def edit_ignore_dirs(self):
        """Open a dialog to edit the ignored directories"""
        dialog = ListEditorDialog(self.root, "Ignored Directories", self.ignore_dirs)
        self.ignore_dirs = dialog.result
        self.log_message(f"Ignored directories updated. {len(self.ignore_dirs)} directories in list.")
    
    def edit_ignore_patterns(self):
        """Open a dialog to edit the ignored file patterns"""
        dialog = ListEditorDialog(self.root, "Ignored File Patterns", self.ignore_patterns)
        self.ignore_patterns = dialog.result
        self.log_message(f"Ignored patterns updated. {len(self.ignore_patterns)} patterns in list.")
    
    def edit_text_obscuration(self):
        """Open dialog to manage text obscuration mappings"""
        dialog = TextObscurationDialog(self.root, self.obscured_words)
        if (dialog.result is not None):
            self.obscured_words = dialog.result
            self.log_message(f"Text obscuration mappings updated. {len(self.obscured_words)} items configured.")
    
    def browse_input_dir(self):
        directory = filedialog.askdirectory(title="Select Input Directory")
        if directory:
            self.input_dir.set(directory)
    
    def browse_output_dir(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir.set(directory)
    
    def load_config(self):
        try:
            if os.path.exists("config_gui.yaml"):
                with open("config_gui.yaml", "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                
                if "dir_path" in config:
                    self.input_dir.set(config["dir_path"])
                if "output_dir" in config:
                    self.output_dir.set(config["output_dir"])
                if "max_tokens" in config:
                    self.max_tokens.set(str(config["max_tokens"]))
                if "include_non_text_files" in config:
                    self.include_non_text.set(config["include_non_text_files"])
                    # Update UI based on this setting
                    self.toggle_non_text_message()
                if "non_text_file_placeholder" in config:
                    self.non_text_placeholder.set(config["non_text_file_placeholder"])
                if "file_template" in config:
                    self.file_template = config["file_template"]
                if "file_separator" in config:
                    self.file_separator = config["file_separator"]
                if "ignore_dirs" in config:
                    self.ignore_dirs = config["ignore_dirs"]
                if "ignore_patterns" in config:
                    self.ignore_patterns = config["ignore_patterns"]
                if "obscured_words" in config:
                    self.obscured_words = config["obscured_words"]
                
                self.log_message("Default configuration loaded from config_gui.yaml")
        except Exception as e:
            self.log_message(f"Error loading configuration: {str(e)}")
    
    def log_message(self, message):
        self.log_area.config(state='normal')  # Temporarily enable writing
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)  # Auto-scroll to bottom
        self.log_area.config(state='disabled')  # Disable writing again
    
    def redirect_stdout(self):
        class StdoutRedirector:
            def __init__(self, text_widget):
                self.text_widget = text_widget
            
            def write(self, string):
                # Use after to safely update the GUI from another thread
                self.text_widget.after(0, self._write, string)
            
            def _write(self, string):
                self.text_widget.config(state='normal')
                self.text_widget.insert(tk.END, string)
                self.text_widget.see(tk.END)
                self.text_widget.config(state='disabled')
            
            def flush(self):
                pass
        
        # Redirect stdout and stderr to the text widget
        sys.stdout = StdoutRedirector(self.log_area)
        sys.stderr = StdoutRedirector(self.log_area)
    
    def get_current_config(self):
        """
        Create a configuration dictionary from the current GUI state without saving to disk.
        This is used for temporary execution without overwriting the config file.
        """
        config = {
            "dir_path": self.input_dir.get(),
            "output_dir": self.output_dir.get(),
            "max_tokens": int(self.max_tokens.get()),
            "include_non_text_files": self.include_non_text.get(),
            "ignore_dirs": self.ignore_dirs,
            "ignore_patterns": self.ignore_patterns,
            "file_separator": self.file_separator,
        }
        
        # Only include non-text placeholder if including non-text files
        if self.include_non_text.get():
            config["non_text_file_placeholder"] = self.non_text_placeholder.get()
        
        # Only include file template if it's not empty
        if self.file_template:
            config["file_template"] = self.file_template
            
        # Include obscured words mappings
        if self.obscured_words:
            config["obscured_words"] = self.obscured_words
        
        return config
    
    def run_concatext(self):
        # Input validation
        if not self.input_dir.get():
            messagebox.showerror("Configuration Error", 
                                "Input directory not specified!\n\n"
                                "You must select an input directory before starting the process.")
            return
        
        if not self.output_dir.get():
            messagebox.showerror("Configuration Error", 
                               "Output directory not specified!\n\n"
                               "You must select an output directory before starting the process.")
            return
        
        try:
            max_tokens = int(self.max_tokens.get())
            if (max_tokens <= 0):
                messagebox.showerror("Error", "Maximum number of tokens must be greater than zero!")
                return
        except ValueError:
            messagebox.showerror("Error", "Maximum number of tokens must be an integer!")
            return
        
        # Ensure directories exist
        input_path = Path(self.input_dir.get())
        output_path = Path(self.output_dir.get())
        
        if not input_path.exists():
            messagebox.showerror("Error", f"Input directory '{input_path}' does not exist!")
            return
        
        # Create output directory if it doesn't exist
        if not output_path.exists():
            try:
                output_path.mkdir(parents=True)
                self.log_message(f"Created output directory: {output_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Unable to create output directory: {str(e)}")
                return
        
        # Start processing in a separate thread
        self.log_message("Starting Concatext processing...")
        
        # Redirect stdout to capture output
        self.redirect_stdout()
        
        # Start the process in a separate thread
        threading.Thread(target=self.process_thread, daemon=True).start()
    
    def process_thread(self):
        try:
            # Get current config from GUI instead of loading from file
            config = self.get_current_config()
            
            # Create and start the processor with current GUI settings
            processor = concatext.DirContentProcessor(config)
            processor.process_dir()
            
            # Show a custom completion dialog with option to open output folder
            self.root.after(0, self.show_completion_dialog)
        except Exception as e:
            error_msg = f"Error during processing: {str(e)}"
            self.log_message(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
    
    def show_completion_dialog(self):
        """Shows a completion message with options to open the output folder"""
        # First make sure the main window's geometry is up to date
        self.root.update_idletasks()
        
        # Get parent window position and size
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_width = self.root.winfo_width()
        parent_height = self.root.winfo_height()
        
        # Use fixed dimensions that ensure all content is visible
        dialog_width = 500
        dialog_height = 220
        
        # Calculate position to center the dialog relative to parent
        pos_x = parent_x + (parent_width // 2) - (dialog_width // 2)
        pos_y = parent_y + (parent_height // 2) - (dialog_height // 2)
        
        # Ensure dialog remains on screen
        pos_x = max(0, pos_x)
        pos_y = max(0, pos_y)
        
        # Create dialog with position already set to avoid flickering
        dialog = tk.Toplevel(self.root)
        dialog.title("Process Completed")
        dialog.geometry(f"{dialog_width}x{dialog_height}+{pos_x}+{pos_y}")
        
        # Make dialog resizable
        dialog.resizable(True, True)
        
        # Set a minimum size
        dialog.minsize(450, 220)
        
        # Make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Apply a solid border
        if sys.platform == "darwin":  # macOS specific styling
            dialog.configure(background='#ececec')  # Match macOS dialog background
        
        # Create a main frame with padding
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top content frame that expands
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Success message with icon (using Unicode character for simplicity and cross-platform support)
        message_frame = ttk.Frame(content_frame)
        message_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Success icon (checkmark)
        success_label = ttk.Label(
            message_frame,
            text="✓",
            font=("", 24, "bold"),  # Increased font size
            foreground="green"
        )
        success_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Success text
        ttk.Label(
            message_frame,
            text="Processing completed successfully!",
            font=("", 16, "bold")  # Increased font size
        ).pack(side=tk.LEFT, fill=tk.X)
        
        # Output folder information with better formatting
        output_path = Path(self.output_dir.get()).resolve()
        path_frame = ttk.Frame(content_frame)
        path_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(
            path_frame,
            text="Output location:",
            font=("", 14)  # Increased font size
        ).pack(anchor=tk.W)
        
        # Display path 
        path_display = ttk.Label(
            path_frame,
            text=str(output_path),
            font=("", 14)  # Increased font size
        )
        path_display.pack(anchor=tk.W, padx=(10, 0))
        
        # Bottom frame that doesn't expand - always stays at bottom
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Add a separator for visual distinction
        ttk.Separator(bottom_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Buttons frame
        button_frame = ttk.Frame(bottom_frame)
        button_frame.pack(fill=tk.X)
        
        # Open folder button with improved styling
        open_button = ttk.Button(
            button_frame, 
            text="Open Output Folder", 
            command=lambda: [self.open_output_folder(), dialog.destroy()]
        )
        open_button.pack(side=tk.LEFT, padx=5)
        
        # Focus on the open button as the default action
        open_button.focus_set()
        
        # Close button
        ttk.Button(
            button_frame, 
            text="Close", 
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)
        
        # Add keyboard shortcuts
        dialog.bind("<Return>", lambda e: [self.open_output_folder(), dialog.destroy()])  # Enter key
        dialog.bind("<Escape>", lambda e: dialog.destroy())  # Escape key
    
    def center_window(self, window):
        """Centers a window relative to its parent"""
        window.update_idletasks()
        
        # Get parent window position and size
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_width = self.root.winfo_width()
        parent_height = self.root.winfo_height()
        
        # Get dialog size
        window_width = window.winfo_width()
        window_height = window.winfo_height()
        
        # Calculate position to center the dialog relative to parent
        pos_x = parent_x + (parent_width // 2) - (window_width // 2)
        pos_y = parent_y + (parent_height // 2) - (window_height // 2)
        
        # Ensure dialog remains on screen
        pos_x = max(0, pos_x)
        pos_y = max(0, pos_y)
        
        # Set position
        window.geometry(f"+{pos_x}+{pos_y}")

    def remove_focus(self, event):
        # Get the widget that was clicked
        widget = event.widget
        
        # If the clicked widget is not an input widget, remove focus from all input widgets
        if not isinstance(widget, (ttk.Entry, tk.Text, tk.Listbox)):
            # Remove focus from all input widgets
            for child in self.root.winfo_children():
                if isinstance(child, (ttk.Entry, tk.Text, tk.Listbox)):
                    child.focus_set()
                    child.focus_force()
            # Set focus back to root window
            self.root.focus_set()

    def clear_log(self):
        """Clears all content from the log area"""
        self.log_area.config(state='normal')  # Temporarily enable writing
        self.log_area.delete("1.0", tk.END)  # Delete all content
        self.log_area.config(state='disabled')  # Disable writing again

    def open_output_folder(self):
        """Opens the output folder in the system's file explorer"""
        output_dir = Path(self.output_dir.get()).resolve()
        
        if not output_dir.exists():
            messagebox.showerror("Error", f"Output directory '{output_dir}' does not exist!")
            return
            
        try:
            # Open folder based on operating system
            if sys.platform == "win32":
                os.startfile(output_dir)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", output_dir])
            else:  # linux/unix
                subprocess.run(["xdg-open", output_dir])
                
            self.log_message(f"Output folder opened: {output_dir}")
        except Exception as e:
            self.log_message(f"Error opening output folder: {str(e)}")
            messagebox.showerror("Error", f"Unable to open output folder: {str(e)}")

def main():
    root = tk.Tk()
    app = ConcatextGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
