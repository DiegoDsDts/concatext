// src/workers/processingWorker.test.js

// Import assertion utilities
import { describe, it, assertEquals, mockFn, getTestSummary } from '../utils/testUtils.js';

// Import functions to be tested and their setters
import {
  apply_obscured_words,
  format_file_block,
  matches_pattern,
  count_tokens,
  _setPostMessage,
  _setEncodeFunction
} from './processingWorker.js';

// Import the actual encoder for default/reset behavior in tests
import { encode as gptEncode } from 'gpt-tokenizer';

// --- Test Execution ---
console.log("Starting tests for processingWorker utilities...");

// Setup mock for postMessage for all tests
const mockedPostMessage = mockFn();
_setPostMessage(mockedPostMessage);

// Reset to actual gptEncode before each 'describe' suite or specific tests if necessary.
// For count_tokens, we'll manage this within its describe block.
_setEncodeFunction(gptEncode);


describe('apply_obscured_words', () => {
  it('should return original text if no obscuration map is provided', () => {
    assertEquals(apply_obscured_words("hello world", {}), "hello world");
    assertEquals(apply_obscured_words("hello world", null), "hello world");
  });

  it('should obscure a single word', () => {
    assertEquals(apply_obscured_words("hello world", { "world": "earth" }), "hello earth");
  });

  it('should obscure multiple different words', () => {
    const text = "hello world, this is a test";
    const map = { "world": "planet", "test": "trial" };
    assertEquals(apply_obscured_words(text, map), "hello planet, this is a trial");
  });

  it('should obscure a word that appears multiple times', () => {
    const text = "test one test two test";
    const map = { "test": "XXX" };
    assertEquals(apply_obscured_words(text, map), "XXX one XXX two XXX");
  });

  it('should be case-insensitive due to /gi flag in regex', () => {
    const text = "Hello hello HELLO";
    const map = { "hello": "hi" };
    assertEquals(apply_obscured_words(text, map), "hi hi hi");
  });
  
  it('should handle word boundaries (e.g. not obscure "testing" if "test" is key)', () => {
    const text = "test testing tester";
    const map = { "test": "XXX" };
    assertEquals(apply_obscured_words(text, map), "XXX testing tester");
  });

  it('should return original text if word not found', () => {
    const text = "hello world";
    const map = { "test": "XXX" };
    assertEquals(apply_obscured_words(text, map), "hello world");
  });

  it('should return empty string if input text is empty', () => {
    assertEquals(apply_obscured_words("", { "hello": "hi" }), "");
  });

  it('should return original text if obscuration map is empty', () => {
    assertEquals(apply_obscured_words("hello world", {}), "hello world");
  });
  
  it('should handle words with special regex characters if map keys are simple strings', () => {
    const text = "hello word. this is a word";
    const map = { "word.": "REPLACED_DOT", "word": "REPLACED_NO_DOT" }; // key "word." becomes /word./gi
    assertEquals(apply_obscured_words(text, map), "hello REPLACED_DOT this is a REPLACED_NO_DOT");
    
    const map2 = { "w.rd": "X" }; // key "w.rd" becomes /w.rd/gi
    assertEquals(apply_obscured_words("word wird ward", map2), "X X X");
  });
});

describe('format_file_block', () => {
  it('should replace all placeholders in a basic template', () => {
    const result = format_file_block("path/to/file.txt", "file.txt", "content here", "{path} | {name} | {content}");
    assertEquals(result, "path/to/file.txt | file.txt | content here");
  });

  it('should handle templates with only some placeholders', () => {
    const result = format_file_block("p", "n", "c", "Name: {name}");
    assertEquals(result, "Name: n");
  });

  it('should handle templates with extra text around placeholders', () => {
    const result = format_file_block("p", "n", "c", "File ({name}) has content: [{content}]");
    assertEquals(result, "File (n) has content: [c]");
  });

  it('should handle empty content, path, or name', () => {
    assertEquals(format_file_block("", "file.txt", "content", "{path}|{name}|{content}"), "|file.txt|content");
    assertEquals(format_file_block("path", "", "content", "{path}|{name}|{content}"), "path||content");
    assertEquals(format_file_block("path", "name", "", "{path}|{name}|{content}"), "path|name|");
  });

  it('should return empty string if template is empty', () => {
    assertEquals(format_file_block("p", "n", "c", ""), "");
  });
  
  it('should handle multiple occurrences of the same placeholder', () => {
    const result = format_file_block("p", "n", "c", "{name} - {name} - {content}");
    assertEquals(result, "n - n - c");
  });
});

describe('matches_pattern', () => {
  it('should perform exact match', () => {
    assertEquals(matches_pattern("file.txt", "file.txt"), true);
    assertEquals(matches_pattern("file.txt", "file.tx"), false);
  });

  it('should match with startsWith pattern (suffix*)', () => {
    assertEquals(matches_pattern("file.txt", "file.*"), true);
    assertEquals(matches_pattern("file.txt", "fil.*"), true);
    assertEquals(matches_pattern("file.txt", "*.txt"), false); 
    assertEquals(matches_pattern("file.txt", "other.*"), false);
  });
  
  it('should match with endsWith pattern (*prefix)', () => {
    assertEquals(matches_pattern("file.txt", "*.txt"), true);
    assertEquals(matches_pattern("file.txt", "*.xt"), true);
    assertEquals(matches_pattern("file.txt", "file.*"), false); 
    assertEquals(matches_pattern("file.txt", "*.txs"), false);
  });

  it('should match with includes pattern (*substring*)', () => {
    assertEquals(matches_pattern("file.name.txt", "*.name.*"), true);
    assertEquals(matches_pattern("filename.txt", "*name.*"), true);
    assertEquals(matches_pattern("file.txt", "*e.t*"), true);
    assertEquals(matches_pattern("file.txt", "*xyz*"), false);
  });

  it('should return false for non-matching patterns', () => {
    assertEquals(matches_pattern("file.txt", "other.txt"), false);
    assertEquals(matches_pattern("file.txt", "f*s"), false);
  });
});

describe('count_tokens', () => {
  // Reset to actual gptEncode before these tests
  _setEncodeFunction(gptEncode);
  const localMockPostMessage = mockFn(); // Use a local mock for this suite if needed
  _setPostMessage(localMockPostMessage);

  it('should return 0 for an empty string', () => {
    assertEquals(count_tokens(""), 0);
  });

  it('should count tokens for a simple sentence', () => {
    assertEquals(count_tokens("Hello world, this is a test."), 8); 
  });

  it('should count tokens for a string with punctuation', () => {
    assertEquals(count_tokens("Test!"), 2); 
    assertEquals(count_tokens("Test, test."), 4);
  });

  it('should call mocked postMessage on tokenizer error and return 0', () => {
    const mockEncodeError = mockFn().mockImplementation(() => {
      throw new Error("Tokenizer failed");
    });
    _setEncodeFunction(mockEncodeError); // Temporarily set faulty encoder

    const result = count_tokens("some text");
    
    assertEquals(result, 0, "Expected count_tokens to return 0 on error.");
    assertEquals(localMockPostMessage.callCount(), 1, "postMessage was not called once on error.");
    
    const calls = localMockPostMessage.getCalls();
    const callArg = calls[0][0]; // First argument of the first call
    assertEquals(callArg.type, 'error', "postMessage type was not 'error'.");
    assertEquals(callArg.message.includes("Tokenization error for a piece of text: Tokenizer failed"), true, "Error message mismatch.");

    _setEncodeFunction(gptEncode); // Reset to actual encoder for subsequent tests
    _setPostMessage(mockedPostMessage); // Reset to the general mock
  });
});


// --- Summary ---
// The getTestSummary function will be called by the script running this file.
// If running directly with node: `node src/workers/processingWorker.test.js`
// And then check the exit code: `echo $?` (0 for success, 1 for failure)
// Or, the script in package.json will handle this.

// To make this file directly executable and print summary:
if (typeof process !== 'undefined' && process.argv.includes(import.meta.url.substring(import.meta.url.lastIndexOf('/') + 1))) {
    const exitCode = getTestSummary();
    if (typeof process.exit === 'function') { // Ensure process.exit exists (it does in Node)
        process.exit(exitCode);
    } else if (exitCode !== 0) { // Fallback for environments without process.exit
        throw new Error("Tests failed!");
    }
}
