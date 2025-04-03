#!/usr/bin/env python3
"""
concatext.py

This script processes a local directory by concatenating its file contents into text files,
with a specified token limit per file.

Usage:
    ./concatext.py [dir_path]

The program uses settings defined in config.yaml in the current path.
If a dir_path is specified via command line, it takes precedence over the value in config.yaml.
"""

import os
import fnmatch
import yaml
import logging
from pathlib import Path
import nltk
from nltk.tokenize import word_tokenize
import ssl
import time
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('concatext')

# Resolve SSL certificate issue for NLTK downloads
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download NLTK data quietly
try:
    nltk.download('punkt', quiet=True)
except Exception as e:
    logger.warning(f"Failed to download NLTK data: {e}")
    logger.warning("Some functionality may be limited")

def format_size(size_bytes):
    """
    Convert bytes to a human-readable string with appropriate units.
    
    Args:
        size_bytes (int): Size in bytes
    
    Returns:
        str: Human-readable size with units (B, KB, MB, GB, TB)
    """
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    
    while size_bytes >= 1024 and unit_index < len(units) - 1:
        size_bytes /= 1024.0
        unit_index += 1
    
    return f"{size_bytes:.2f} {units[unit_index]}"

def load_config(config_path='config.yaml', override_dir_path=None):
    """
    Load configuration from a YAML file.
    
    Args:
        config_path (str): Path to the configuration file
        override_dir_path (str, optional): If specified, overrides the dir_path from the config file
    
    Returns:
        dict: The loaded configuration
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as config_file:
            config = yaml.safe_load(config_file)
            logger.info(f"Configuration loaded from '{config_path}'")
    except FileNotFoundError:
        logger.error(f"Error: Configuration file '{config_path}' not found.")
        exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file: {e}")
        exit(1)
    
    # If a directory path was specified from the command line, use it
    if override_dir_path:
        config["dir_path"] = override_dir_path
        logger.info(f"Using directory path from command line: {override_dir_path}")
    
    # Check required parameters
    if "dir_path" not in config:
        logger.error("Error: 'dir_path' not specified. Please provide an input directory path either:\n"
                     "1. As a command line argument: ./concatext.py /path/to/directory\n"
                     "2. In the config.yaml file: dir_path: \"/path/to/directory\"")
        exit(1)
    
    # Set default values if missing
    if "max_tokens" not in config:
        config["max_tokens"] = 200000
    if "output_dir" not in config:
        config["output_dir"] = "."
    if "ignore_dirs" not in config:
        config["ignore_dirs"] = []
    if "ignore_patterns" not in config:
        config["ignore_patterns"] = []
    if "file_template" not in config:
        # Default template matching the original format
        config["file_template"] = "===\n{path}\n===\n{content}\n==="
    if "include_non_text_files" not in config:
        config["include_non_text_files"] = True
    if "non_text_file_placeholder" not in config:
        config["non_text_file_placeholder"] = "non-text file placeholder"
    if "file_separator" not in config:
        config["file_separator"] = "\n\n"  # Default separator between files
    
    return config


class DirContentProcessor:
    def __init__(self, config):
        self.dir_path = Path(config["dir_path"]).resolve()
        self.content = ""
        self.file_counter = 1
        self.current_token_count = 0
        self.current_source_files = 0  # Counter for source files in the current output file
        self.MAX_TOKENS = config["max_tokens"]
        self.non_text_files_count = 0  # Counter for non-text files
        self.start_time = time.time()
        self.output_files = []  # Tracks generated output files
        
        # Set the output directory
        self.output_dir = Path(config["output_dir"]).resolve()

        # Get the directory name for output file naming
        self.dir_name = self.dir_path.name
        
        # Configuration for files/directories to ignore
        self.ignore_dirs = set(config["ignore_dirs"])
        self.ignore_patterns = set(config["ignore_patterns"])

        # Store the file template
        self.file_template = config["file_template"]
        
        # Store the file separator
        self.file_separator = config["file_separator"]
        
        # Configuration for non-text files
        self.include_non_text_files = config["include_non_text_files"]
        self.non_text_file_placeholder = config["non_text_file_placeholder"]

    def format_file_block(self, relative_path, file_content):
        """Returns a formatted text block using the template from config."""
        # Get just the filename from the path
        file_name = os.path.basename(relative_path)
        
        # Replace the template placeholders
        formatted_block = self.file_template.replace("{path}", str(relative_path))
        formatted_block = formatted_block.replace("{name}", file_name)
        formatted_block = formatted_block.replace("{content}", file_content)
        
        return formatted_block

    def count_tokens(self, text):
        """Count tokens in text using NLTK tokenizer."""
        return len(word_tokenize(text, language='english', preserve_line=True))

    def save_current_content(self):
        """Save accumulated content to a text file and reset the buffer."""
        if self.content.strip():
            # Format the counter with at least 2 digits
            counter_str = f"{self.file_counter:02d}"
            output_file = self.output_dir / f'{self.dir_name}_{counter_str}.txt'
            
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(self.content.rstrip() + "\n")
                
                # Get file size
                file_size = os.path.getsize(output_file)
                
                # Store output file info
                self.output_files.append({
                    'filename': str(output_file),
                    'token_count': self.current_token_count,
                    'file_size': file_size,
                    'source_file_count': self.current_source_files  # Store the count
                })
                
                logger.info(f"Created {output_file} with {self.current_token_count:,} tokens from {self.current_source_files} files.")
                self.file_counter += 1
                self.content = ""
                self.current_token_count = 0
                self.current_source_files = 0  # Reset the source file counter
            except IOError as e:
                logger.error(f"Error writing to file {output_file}: {e}")

    def process_file(self, file_path):
        """Read and add file content, respecting the token limit."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read().rstrip()
        except (UnicodeDecodeError, IOError) as e:
            # Check if we should include non-text files
            if not self.include_non_text_files:
                # Skip this file completely
                self.non_text_files_count += 1
                logger.warning(f"Skipping non-text file {file_path}: {str(e)}")
                return
                
            # Include the file with a placeholder message
            error_message = f"{self.non_text_file_placeholder}"
            file_content = error_message
            self.non_text_files_count += 1
            logger.warning(f"Non-text file {file_path}: {str(e)}")

        relative_path = str(file_path.relative_to(self.dir_path))
        path_block = self.format_file_block(relative_path, file_content)
        
        # Add separator if not the first file in the content
        if self.content and self.file_separator:
            separator_token_count = self.count_tokens(self.file_separator)
            # Check if adding separator would exceed limit
            if self.current_token_count + separator_token_count > self.MAX_TOKENS:
                self.save_current_content()
                block_token_count = self.count_tokens(path_block)
            else:
                # Add separator and update token count
                self.content += self.file_separator
                self.current_token_count += separator_token_count
                block_token_count = self.count_tokens(path_block)
        else:
            block_token_count = self.count_tokens(path_block)

        # If adding this block exceeds the limit, save and restart
        if self.current_token_count + block_token_count > self.MAX_TOKENS:
            self.save_current_content()

        self.content += path_block
        self.current_token_count += block_token_count
        self.current_source_files += 1 # Increment source file counter for this output file

    def print_summary(self, file_count, ignored_files_count, ignored_dirs_count):
        """Print a comprehensive summary of the processing results."""
        end_time = time.time()
        execution_time = end_time - self.start_time
        
        # Calculate totals
        total_tokens = sum(f['token_count'] for f in self.output_files)
        total_size = sum(f['file_size'] for f in self.output_files)
        total_source_files = sum(f['source_file_count'] for f in self.output_files)  # Calculate total source files
        
        # Print header
        print("\n" + "="*80)
        print(f"{'CONCATEXT EXECUTION SUMMARY':^80}")
        print("="*80)
        
        # Process information
        print(f"\nINFORMATION")
        print(f"  • Start Time: {datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  • Execution time: {execution_time:.2f} seconds")
        print(f"  • Directory name: {self.dir_path.name}")
        print(f"  • Max tokens / file: {self.MAX_TOKENS:,}")
        
        # File statistics
        print(f"\nSTATISTICS")
        print(f"  • Processed files: {file_count}")
        # Determine the status message based on the configuration
        non_text_status = "(included)" if self.include_non_text_files else "(not included)"
        print(f"  • Non-text files: {self.non_text_files_count} {non_text_status}")
        print(f"  • Ignored files: {ignored_files_count}")
        print(f"  • Ignored directories: {ignored_dirs_count}")
        
        # Output files
        print(f"\nOUTPUT ({len(self.output_files)})")
        for idx, file_info in enumerate(self.output_files, 1):
            print(f"  {idx}. {file_info['filename']}")
            print(f"     - Tokens: {file_info['token_count']:,}")
            print(f"     - Size: {format_size(file_info['file_size'])}")
            print(f"     - Source files: {file_info['source_file_count']}")
        
        # Totals
        print(f"\nTOTALS")
        print(f"  • Total tokens: {total_tokens:,}")
        print(f"  • Total output size: {format_size(total_size)}")
        print(f"  • Total source files: {total_source_files}")  # Display total source files
        
        print("\n" + "="*80)
        print(f"{'END OF CONCATEXT EXECUTION':^80}")
        print("="*80 + "\n")

    def process_dir(self):
        """Process all files in the directory."""
        if not self.dir_path.exists():
            logger.error(f"Error: Directory '{self.dir_path}' does not exist.")
            exit(1)

        logger.info(f"Starting scan of: {self.dir_path}")
        file_count = 0
        ignored_files_count = 0
        ignored_dirs_count = 0

        for root, dirs, files in os.walk(self.dir_path):
            # Skip ignored directories
            dirs_to_ignore = [d for d in dirs if d in self.ignore_dirs]
            for d in dirs_to_ignore:
                logger.info(f"Ignoring directory: {os.path.join(os.path.basename(root), d)}")
            
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            ignored_dirs_count += len(dirs_to_ignore)

            for file in files:
                file_path = Path(root) / file
                relative_path = file_path.relative_to(self.dir_path)

                # Skip files matching ignore patterns
                if any(fnmatch.fnmatch(str(relative_path), pattern) for pattern in self.ignore_patterns):
                    ignored_files_count += 1
                    logger.info(f"Ignoring file: {relative_path}")
                    continue

                logger.info(f"Processing file: {relative_path}")
                self.process_file(file_path)
                file_count += 1

        # Save any remaining content
        if self.content:
            self.save_current_content()

        self.print_summary(file_count, ignored_files_count, ignored_dirs_count)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Process a directory and concatenate its contents into text files.')
    parser.add_argument('dir_path', nargs='?', help='Path to the directory to process')
    return parser.parse_args()

def main():
    """Main function."""
    args = parse_arguments()
    config = load_config(override_dir_path=args.dir_path)
    processor = DirContentProcessor(config)
    processor.process_dir()

if __name__ == "__main__":
    main()
