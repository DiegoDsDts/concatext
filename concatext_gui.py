#!/usr/bin/env python3
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

class ConcatextGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Concatext")
        self.root.geometry("580x740")
        self.root.minsize(580, 600)
        
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
        ttk.Button(ignore_buttons_frame, text="Files", width=10, command=self.edit_ignore_patterns).pack(side=tk.RIGHT, padx=2)
        ttk.Button(ignore_buttons_frame, text="Folders", width=10, command=self.edit_ignore_dirs).pack(side=tk.RIGHT, padx=2)
        
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
        ttk.Button(template_buttons_frame, text="File Separator", width=10, command=self.edit_separator).pack(side=tk.RIGHT, padx=2)
        ttk.Button(template_buttons_frame, text="File Template", width=10, command=self.edit_template).pack(side=tk.RIGHT, padx=2)
        
        # Non-text file options
        unsupported_frame = ttk.Frame(advanced_config_frame)
        unsupported_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.unsupported_checkbox = ttk.Checkbutton(
            unsupported_frame, 
            text="Include non-text files", 
            variable=self.include_non_text,
            command=self.toggle_non_text_message
        )
        self.unsupported_checkbox.pack(anchor=tk.W)
        
        # Reformat the non-text message section to exactly match other frames
        self.non_text_msg_frame = ttk.Frame(unsupported_frame)
        self.non_text_msg_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(self.non_text_msg_frame, text="non-text file placeholder:").pack(side=tk.LEFT, padx=(0, 10))
        
        # Add a dedicated button frame like in other sections
        unsupported_btn_frame = ttk.Frame(self.non_text_msg_frame)
        unsupported_btn_frame.pack(side=tk.RIGHT)
        
        self.edit_non_text_msg_button = ttk.Button(unsupported_btn_frame, text="Edit Message", width=10, command=self.edit_non_text_message)
        self.edit_non_text_msg_button.pack(side=tk.RIGHT, padx=2)
        
        # Initially hide the frame if include_non_text is False
        if not self.include_non_text.get():
            self.non_text_msg_frame.pack_forget()
        
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
        """Show or hide the non-text message frame based on checkbox state"""
        if self.include_non_text.get():
            # Show the non-text message frame
            self.non_text_msg_frame.pack(fill=tk.X, padx=5, pady=5)
            self.edit_non_text_msg_button.configure(state='normal')
        else:
            # Hide the non-text message frame
            self.non_text_msg_frame.pack_forget()
    
    def edit_template(self):
        """Open a dialog to edit the file template"""
        dialog = TemplateEditorDialog(self.root, self.file_template)
        if dialog.result is not None:
            self.file_template = dialog.result
            self.log_message("File template updated.")
    
    def edit_separator(self):
        """Open a dialog to edit the file separator"""
        dialog = SeparatorEditorDialog(self.root, self.file_separator)
        if dialog.result is not None:
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
        
        return config
    
    def run_concatext(self):
        # Input validation
        if not self.input_dir.get():
            messagebox.showerror("Configuration Error", 
                                "Input directory not specified!\n\n"
                                "You must select an input directory before starting the process.\n"
                                "Use the 'Browse...' button next to the 'Input Directory' field.")
            return
        
        if not self.output_dir.get():
            messagebox.showerror("Configuration Error", 
                               "Output directory not specified!\n\n"
                               "You must select an output directory before starting the process.\n"
                               "Use the 'Browse...' button next to the 'Output Directory' field.")
            return
        
        try:
            max_tokens = int(self.max_tokens.get())
            if max_tokens <= 0:
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
            
            # Show a message on completion
            self.root.after(0, lambda: messagebox.showinfo("Completed", "Processing completed successfully!"))
        except Exception as e:
            error_msg = f"Error during processing: {str(e)}"
            self.log_message(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))

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
                    child.focus_set()
                    child.focus_force()
            # Set focus back to root window
            self.root.focus_set()

    def clear_log(self):
        """Clears all content from the log area"""
        self.log_area.config(state='normal')  # Temporarily enable writing
        self.log_area.delete("1.0", tk.END)  # Delete all content
        self.log_area.config(state='disabled')  # Disable writing again

def main():
    root = tk.Tk()
    app = ConcatextGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 