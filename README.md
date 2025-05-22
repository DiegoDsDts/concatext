# Concatext - Solid.JS Web Version

**Concatext** is a client-side web application for concatenating the contents of a local directory into structured text files. It's designed to help process codebases and directories into a format that can be easily consumed by LLMs (Large Language Models) or other text processing tools, inspired by an original Python project. All processing is done in your browser, ensuring your files remain private.

## Features

-   **Client-Side Processing**: All file selection, processing, and concatenation happen directly in your web browser. No files are uploaded to any server.
-   **Directory Selection**: Uses the browser's built-in capabilities to select local directories.
-   **Configurable Token Limits**: Automatically splits the output into multiple files based on a configurable token count per chunk, powered by `gpt-tokenizer`.
-   **Customizable Output Formatting**:
    -   **File Template**: Define a custom template for how each file's content (path, name, actual content) is formatted in the output.
    -   **File Separator**: Specify custom text to be inserted between each concatenated file block.
-   **Advanced Filtering**:
    -   **Ignore Directories**: Specify a list of directory names (e.g., `node_modules`, `.git`) to exclude from processing.
    -   **Ignore File Patterns**: Define file patterns (e.g., `*.log`, `package-lock.json`) to ignore specific files.
-   **Text Obscuration**: Replace sensitive words or patterns with placeholders (e.g., API keys, personal information) to protect privacy.
-   **Non-Text File Handling**: Option to include a placeholder for non-text/binary files or skip them entirely.
-   **Download Results**:
    -   Download generated output chunks as individual `.txt` files.
    -   Download all chunks conveniently packaged into a single `.zip` archive.
-   **Configuration Persistence**: All your settings (token limits, templates, ignore lists, etc.) are automatically saved in your browser's local storage for your convenience.

## How to Use (Web Application)

1.  **Access the Application**:
    *   If deployed, open the provided application URL in your web browser.
    *   To run locally, follow the "Running Locally" instructions below and open `http://localhost:3000` (or the specified port).

2.  **Select Input Directory**:
    *   Click the "Select Folder" button.
    *   Your browser's file dialog will appear; choose the local directory you want to process.

3.  **Configure Options**:
    *   Adjust settings in the "Configuration" panel on the left:
        *   **Max Tokens per Chunk**: Set the maximum number of tokens (estimated by `gpt-tokenizer`) for each output file.
        *   **Include Non-Text Files**: Check this to include placeholders for binary/non-text files. Uncheck to skip them.
        *   **Non-Text File Placeholder**: If including non-text files, customize the placeholder text.
        *   **Advanced Formatting**: Click "Edit File Template" or "Edit File Separator" to open modal dialogs for customizing these settings.
        *   **Filtering & Obscuration**: Use the "Edit..." buttons to manage lists of ignored directories, ignored file patterns, and word/placeholder mappings for text obscuration.

4.  **Start Processing**:
    *   Once configured, click the "Start Processing" button.
    *   The configuration panel will be disabled during processing.

5.  **Monitor Progress**:
    *   View real-time progress, logs, and any error messages in the "Log / Progress" area on the right.

6.  **Download Output**:
    *   After processing is complete, download links will appear in the "Download Output Chunks" area.
    *   If multiple chunks are generated, a `.zip` file containing all chunks will be offered. If only one chunk is produced, a single `.txt` file will be available.

## Configuration Details

The following options can be configured directly in the UI:

-   **Max Tokens per Chunk**: Maximum token count for each output text file.
-   **Include Non-Text Files**: Boolean to include or skip binary/non-text files.
-   **Non-Text File Placeholder**: Template string for non-text file content (uses `{name}` and `{path}`).
-   **File Template**: String template for formatting each file block (placeholders: `{path}`, `{name}`, `{content}`).
-   **File Separator**: String to insert between concatenated files.
-   **Ignored Directories**: List of directory names to skip.
-   **Ignored File Patterns**: List of file name patterns (supports basic wildcards like `*name*`, `name*`, `*name`) to skip.
-   **Obscured Words**: A map of words/patterns to their desired placeholder text.

All these settings are automatically saved to your browser's local storage, so they will be remembered the next time you use the application.

## Tokenization Note

This web application uses the `gpt-tokenizer` library for counting tokens. This library is designed to match the tokenization behavior of OpenAI's GPT models (specifically, `cl100k_base` for models like GPT-3.5 and GPT-4). This ensures that the token limits you set correspond closely to how these LLMs would count tokens. This differs from the NLTK library that might have been used in other (e.g., Python) versions of similar tools.

## Running Locally (Development Setup)

To run Concatext (Solid.JS Web Version) on your local machine:

1.  **Prerequisites**:
    *   Node.js (version 18.x or later recommended)
    *   npm (usually comes with Node.js) or pnpm/yarn.

2.  **Get the Code**:
    *   Clone the repository:
        ```bash
        git clone <repository_url>
        cd concatext-solidjs 
        ```
    *   Or download and extract the source code.

3.  **Install Dependencies**:
    *   Navigate to the project directory (`concatext-solidjs`) and run:
        ```bash
        npm install
        ```
        (Or `pnpm install` / `yarn install` if you prefer those package managers).

4.  **Run Development Server**:
    *   Execute the following command:
        ```bash
        npm run dev
        ```
        (Or `pnpm dev` / `yarn dev`).

5.  **Access the Application**:
    *   Open your web browser and go to `http://localhost:3000` (or the port indicated in your terminal, usually 3000).

## Build for Production (Optional)

To create an optimized build of the application for deployment:

1.  **Build Command**:
    ```bash
    npm run build
    ```
2.  The production-ready files will be generated in the `dist` directory. These static files can then be deployed to any web server or static hosting service.

## License

This project is released under the MIT License. See the `LICENSE` file for details (if one is present in the repository).
