# Concatext

**Concatext** is a utility tool for concatenating the contents of a local directory into structured text files with a configurable token limit. It's designed to help process codebases and directories into a format that can be easily consumed by LLMs (Large Language Models) or other text processing tools.

## Features

- **Command Line Interface** - Process directories through a simple command-line tool
- **Graphical User Interface** - User-friendly GUI for configuring and running processes
- **Smart Token Management** - Automatically splits output into multiple files based on token count
- **Configurable Output** - Control how files are formatted in the output
- **Customizable Filtering** - Skip specific directories and file patterns
- **Output Templating** - Custom formatting of file blocks with support for placeholders
- **Non-text File Handling** - Option to include or exclude binary/non-text files
- **Text Obscuration** - Replace sensitive words with placeholders to protect private information

## Requirements

- Python 3.6+
- NLTK library (for tokenization)
- PyYAML (for configuration)
- Tkinter (for GUI)

## Installation

1. Clone the repository
2. Install the required dependencies:

   ```
   pip install nltk pyyaml
   ```
3. Ensure Tkinter is installed (usually comes with Python)

## Usage

### Command Line Interface

Process a directory with default settings:

```
python concatext.py /path/to/directory
```

The script uses settings defined in `config.yaml` in the current directory. If a directory path is specified via command line, it takes precedence over the value in the config file.

### Graphical User Interface

Launch the GUI application:

```
python concatext_gui.py
```

With the GUI, you can:

- Select input and output directories
- Configure token limits
- Edit ignored directories and file patterns
- Customize file templates and separators
- Process directories with a click of a button

### GUI Text Obscuration

Using the graphical interface, you can define mappings for text obscuration:

1. Click on the "Edit" button in the "Obscuration" section under Advanced Configuration
2. Add word-to-placeholder mappings where sensitive words will be replaced with placeholders
   - Example: When you add `password` → `XXXXX`, any occurrence of "password" in the files will be replaced with "XXXXX"
   - Example: When you add `admin@example.com` → `[EMAIL]`, all instances of that email will be replaced with "[EMAIL]"
3. All occurrences of the defined sensitive words will be replaced with their placeholders in the output files

This feature is useful for:
- Protecting sensitive information when sharing code
- Removing personally identifiable information
- Anonymizing data before processing

## Configuration

Concatext can be configured using YAML configuration files:

- **config.yaml** - Configuration for the command-line version
- **config_gui.yaml** - Configuration for the GUI version

### Available Configuration Options

```yaml
# Maximum number of tokens per output file
max_tokens: 250000

# Directory to save output files
output_dir: "./output"

# Include files that are not readable as text (can't be decoded)
include_non_text_files: true

# Placeholder text for non-text files
non_text_file_placeholder: "This file format is not supported or cannot be decoded."

# Separator text between files
file_separator: "\n\n"

# Directories to ignore
ignore_dirs:
  - node_modules
  - .git
  - .vscode

# File patterns to ignore
ignore_patterns:
  - ".DS_Store"
  - ".gitignore"
  - "package-lock.json"

# Template for formatting file blocks
file_template: |
  ========================================
  {path} - start
  ***========================================***
  {content}
  ***========================================***
  {name} - end
  ========================================

# Obscured words configuration
# Define mappings to replace sensitive words with placeholders in the output
# format: word: placeholder
obscured_words:
  # Example (uncomment and modify as needed):
  # password: "XXXXX"
  # username: "USER"
```

## Output Format

The tool generates output files with a naming pattern based on the input directory name. Each file in the output contains formatted content from the source files, structured according to the template defined in the configuration.
````
