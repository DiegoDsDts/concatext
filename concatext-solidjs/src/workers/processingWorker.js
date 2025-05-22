// Content from Subtask 2, Turn 12 (finalized processingWorker.js)
// with exports and dependency injection for testing added.

import { encode as gptEncode } from 'gpt-tokenizer'; // Standard import

// Dependency injection for testing
let currentPostMessage = typeof self !== 'undefined' ? self.postMessage : () => {};
let currentEncode = gptEncode;

export function _setPostMessage(fn) {
  currentPostMessage = fn;
}
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


// 4. Main Worker Logic (onmessage handler - not unit tested directly)
if (typeof self !== 'undefined') {
  self.onmessage = async (event) => {
    const { files: rawFiles, config } = event.data;
    const files = Array.from(rawFiles);

    if (!config) {
      currentPostMessage({ type: 'error', message: 'Configuration not provided to worker.' });
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
    let filesProcessedForProgress = 0; // Separate counter for progress reporting

    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const relativePath = file.webkitRelativePath || file.name;

        filesProcessedForProgress++;
        currentPostMessage({ type: 'progress', file: file.name, summary: { processedFiles: filesProcessedForProgress -1, totalFiles: files.length } });
        
        if (ignore_dirs.some(dir => relativePath.startsWith(dir))) {
          currentPostMessage({ type: 'log', message: `Skipping (ignored dir): ${relativePath}` });
          continue;
        }

        if (ignore_patterns.some(pattern => matches_pattern(file.name, pattern) || matches_pattern(relativePath, pattern))) {
          currentPostMessage({ type: 'log', message: `Skipping (ignored pattern): ${relativePath}` });
          continue;
        }

        let fileContent;
        try {
          const isLikelyBinary = file.type && !file.type.startsWith('text/') && !file.type.includes('json') && !file.type.includes('xml') && !file.type.includes('javascript') && !file.type.includes('csv');
          if (isLikelyBinary) {
              if (include_non_text_files) {
                  fileContent = non_text_file_placeholder;
                  currentPostMessage({ type: 'log', message: `Using placeholder for non-text file: ${relativePath}` });
              } else {
                  currentPostMessage({ type: 'log', message: `Skipping non-text file: ${relativePath}` });
                  continue;
              }
          } else {
               fileContent = await file.text();
          }
        } catch (error) {
          if (include_non_text_files) {
            fileContent = non_text_file_placeholder;
            currentPostMessage({ type: 'log', message: `Error reading file ${relativePath}, using placeholder. Error: ${error.message}` });
          } else {
            currentPostMessage({ type: 'log', message: `Skipping file (read error): ${relativePath}. Error: ${error.message}` });
            continue;
          }
        }

        const processed_content = apply_obscured_words(fileContent, obscured_words);
        const formatted_block = format_file_block(relativePath, file.name, processed_content, file_template);
        const block_token_count = count_tokens(formatted_block);

        if (block_token_count === 0 && formatted_block.length > 0 && fileContent !== non_text_file_placeholder) {
            currentPostMessage({ type: 'log', message: `Warning: File ${file.name} (path: ${relativePath}) resulted in zero tokens but has actual content. Check template or tokenizer.`});
        }

        const separator_token_count = count_tokens(file_separator);

        if (block_token_count > max_tokens) {
          currentPostMessage({ type: 'log', message: `Warning: File ${relativePath} (${block_token_count} tokens) is larger than max_tokens (${max_tokens}). It will be in its own chunk.` });
          if (current_chunk_content) {
            output_chunks.push(current_chunk_content);
            total_tokens_generated += current_token_count;
            current_chunk_content = "";
            current_token_count = 0;
          }
          output_chunks.push(formatted_block);
          total_tokens_generated += block_token_count;
        } else {
          let needed_tokens_for_block = block_token_count;
          if (current_chunk_content) {
            needed_tokens_for_block += separator_token_count;
          }

          if (current_token_count + needed_tokens_for_block > max_tokens) {
            if (current_chunk_content) {
              output_chunks.push(current_chunk_content);
              total_tokens_generated += current_token_count;
            }
            current_chunk_content = formatted_block;
            current_token_count = block_token_count;
          } else {
            if (current_chunk_content) {
              current_chunk_content += file_separator + formatted_block;
              current_token_count += separator_token_count + block_token_count;
            } else {
              current_chunk_content = formatted_block;
              current_token_count = block_token_count;
            }
          }
        }
        total_files_processed++;
      }

      if (current_chunk_content) {
        output_chunks.push(current_chunk_content);
        total_tokens_generated += current_token_count;
      }

      currentPostMessage({
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
      currentPostMessage({ type: 'error', message: `Worker error: ${error.message || error.toString()}` });
    }
  };
}
