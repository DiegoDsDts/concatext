import { encode as gptEncode } from 'gpt-tokenizer';

// Default postMessage function for worker context
let currentPostMessage = globalThis.postMessage;

// Allow overriding postMessage for testing or other contexts
export function _setPostMessage(fn) {
  currentPostMessage = fn;
}
// Allow overriding encode function for testing (e.g. if tokenizer is heavy)
let currentEncode = gptEncode;
export function _setEncodeFunction(fn) {
    currentEncode = fn;
}


// 1. Tokenizer Setup
export function count_tokens(text) {
  try {
    return currentEncode(text).length;
  } catch (error) {
    console.error("Error tokenizing text:", error);
    if (currentPostMessage) {
        currentPostMessage({ type: 'error', message: `Tokenization error for a piece of text: ${error.message}. Content might be incomplete.` });
    }
    return 0; 
  }
}

// 2. Text Obscuration
export function apply_obscured_words(text, obscuration_map) {
  if (!obscuration_map || Object.keys(obscuration_map).length === 0) {
    return text;
  }
  let modified_text = text;
  for (const word in obscuration_map) {
    if (Object.hasOwnProperty.call(obscuration_map, word)) {
      const placeholder = obscuration_map[word];
      // Using regex for whole-word matching, case-insensitive
      const regex = new RegExp(`\\b${word}\\b`, 'gi');
      modified_text = modified_text.replace(regex, placeholder);
    }
  }
  return modified_text;
}

// 3. File Block Formatting
export function format_file_block(relativePath, fileName, fileContent, template) {
  let formatted_block = template;
  formatted_block = formatted_block.replace(/{path}/g, relativePath);
  formatted_block = formatted_block.replace(/{name}/g, fileName);
  formatted_block = formatted_block.replace(/{content}/g, fileContent);
  return formatted_block;
}

// Helper for pattern matching (simple version)
export function matches_pattern(text, pattern) {
    if (pattern.startsWith('*') && pattern.endsWith('*')) {
        return text.includes(pattern.slice(1, -1));
    } else if (pattern.startsWith('*')) {
        return text.endsWith(pattern.substring(1));
    } else if (pattern.endsWith('*')) {
        return text.startsWith(pattern.slice(0, -1));
    }
    return text === pattern;
}


// 4. Main Worker Logic
self.onmessage = async (event) => {
  const { files: rawFiles, config } = event.data;
  // Convert FileList to Array if necessary
  const files = Array.from(rawFiles);


  if (!config) {
    postMessage({ type: 'error', message: 'Configuration not provided to worker.' });
    return;
  }

  const {
    max_tokens,
    ignore_dirs = [],
    ignore_patterns = [],
    file_template,
    file_separator,
    include_non_text_files,
    non_text_file_placeholder,
    obscured_words = {}
  } = config;

  let output_chunks = [];
  let current_chunk_content = "";
  let current_token_count = 0;
  let total_files_processed = 0;
  let total_tokens_generated = 0;

  try {
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const relativePath = file.webkitRelativePath || file.name; // webkitRelativePath for folders

      postMessage({ type: 'progress', file: file.name, processedFiles: i, totalFiles: files.length });

      // Filtering by ignore_dirs
      if (ignore_dirs.some(dir => relativePath.startsWith(dir))) {
        postMessage({ type: 'log', message: `Skipping (ignored dir): ${relativePath}` });
        continue;
      }

      // Filtering by ignore_patterns
      if (ignore_patterns.some(pattern => matches_pattern(file.name, pattern) || matches_pattern(relativePath, pattern))) {
        postMessage({ type: 'log', message: `Skipping (ignored pattern): ${relativePath}` });
        continue;
      }

      let fileContent;
      try {
        // Check if the file type indicates a binary file.
        // This is a basic check; more robust checks might be needed.
        const isLikelyBinary = file.type && !file.type.startsWith('text/') && !file.type.includes('json') && !file.type.includes('xml') && !file.type.includes('javascript') && !file.type.includes('csv');

        if (isLikelyBinary) {
            if (include_non_text_files) {
                fileContent = non_text_file_placeholder;
                postMessage({ type: 'log', message: `Using placeholder for non-text file: ${relativePath}` });
            } else {
                postMessage({ type: 'log', message: `Skipping non-text file: ${relativePath}` });
                continue;
            }
        } else {
             fileContent = await file.text();
        }
      } catch (error) {
        // Error reading file as text
        if (include_non_text_files) {
          fileContent = non_text_file_placeholder;
          postMessage({ type: 'log', message: `Error reading file ${relativePath}, using placeholder. Error: ${error.message}` });
        } else {
          postMessage({ type: 'log', message: `Skipping file (read error): ${relativePath}. Error: ${error.message}` });
          continue;
        }
      }

      const processed_content = apply_obscured_words(fileContent, obscured_words);
      const formatted_block = format_file_block(relativePath, file.name, processed_content, file_template);
      const block_token_count = count_tokens(formatted_block);

      if (block_token_count === 0 && formatted_block.length > 0 && fileContent !== non_text_file_placeholder) { // Avoid warning for placeholders
          postMessage({ type: 'log', message: `Warning: File ${file.name} (path: ${relativePath}) resulted in zero tokens but has actual content. Check template or tokenizer.`});
      }

      // Chunk Management - Refactored based on prompt
      const separator_token_count = count_tokens(file_separator); // Calculate once

      // Case 1: The current file block itself is larger than max_tokens
      if (block_token_count > max_tokens) {
        postMessage({ type: 'log', message: `Warning: File ${relativePath} (${block_token_count} tokens) is larger than max_tokens (${max_tokens}). It will be in its own chunk.` });
        // If there's existing content in current_chunk, push it first
        if (current_chunk_content) {
          output_chunks.push(current_chunk_content);
          total_tokens_generated += current_token_count;
          current_chunk_content = "";
          current_token_count = 0;
        }
        // Add the large block as its own chunk
        output_chunks.push(formatted_block);
        total_tokens_generated += block_token_count;
        // current_chunk_content and current_token_count remain 0 for the next file
      } else {
        // Case 2: The current block can fit into max_tokens (it's not oversized by itself)

        // Check if adding the new block (plus separator if needed) would exceed max_tokens
        let needed_tokens_for_block = block_token_count;
        if (current_chunk_content) { // If chunk isn't empty, we'll need a separator
          needed_tokens_for_block += separator_token_count;
        }

        if (current_token_count + needed_tokens_for_block > max_tokens) {
          // It would exceed. Push the current chunk.
          if (current_chunk_content) { // Ensure there's something to push
            output_chunks.push(current_chunk_content);
            total_tokens_generated += current_token_count;
          }
          // Start new chunk with the current file block
          current_chunk_content = formatted_block;
          current_token_count = block_token_count;
        } else {
          // It fits. Append to the current chunk.
          if (current_chunk_content) {
            current_chunk_content += file_separator + formatted_block;
            current_token_count += separator_token_count + block_token_count;
          } else {
            // Current chunk is empty, start it with this block
            current_chunk_content = formatted_block;
            current_token_count = block_token_count;
          }
        }
      }
      total_files_processed++;
    }

    // Finalization
    if (current_chunk_content) {
      output_chunks.push(current_chunk_content);
      total_tokens_generated += current_token_count;
    }

    postMessage({
      type: 'result',
      output_chunks: output_chunks,
      summary: {
        totalFilesProcessed: total_files_processed,
        totalFilesSelected: files.length,
        totalTokensGenerated: total_tokens_generated,
        outputChunkCount: output_chunks.length
      }
    });

  } catch (error) {
    console.error("Error in worker:", error);
    postMessage({ type: 'error', message: `Worker error: ${error.message || error.toString()}` });
  }
};
