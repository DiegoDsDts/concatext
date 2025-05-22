// src/App.jsx
import { createSignal, Show, For, onMount, createEffect, onCleanup } from 'solid-js';
import JSZip from 'jszip'; // Import JSZip
import styles from './App.module.css';
import FileInput from './components/FileInput';
import TemplateEditorModal from './components/modals/TemplateEditorModal';
import SeparatorEditorModal from './components/modals/SeparatorEditorModal';
import ListEditorModal from './components/modals/ListEditorModal';
import ObscurationEditorModal from './components/modals/ObscurationEditorModal';

const LOCAL_STORAGE_KEY = 'concatextConfig';

const DEFAULT_CONFIG = {
  maxTokens: 4000,
  includeNonTextFiles: false,
  nonTextFilePlaceholder: "[Content of non-text file: {name}]",
  fileTemplate: "File: {name}\nRelative Path: {path}\n\n{content}",
  fileSeparator: "\n\n--- Next File ---\n\n",
  ignoreDirs: ["node_modules", ".git", "dist", "build"],
  ignorePatterns: ["*.log", ".DS_Store", "package-lock.json", "*.tmp"],
  obscuredWords: { "secret": "XXXXX" },
};

function App() {
  // 1. Define Configuration Signals
  const [inputDirName, setInputDirName] = createSignal("");
  const [selectedFiles, setSelectedFiles] = createSignal(null); // FileList object
  const [isProcessing, setIsProcessing] = createSignal(false); // For disabling UI during processing
  const [maxTokens, setMaxTokens] = createSignal(DEFAULT_CONFIG.maxTokens);
  const [includeNonTextFiles, setIncludeNonTextFiles] = createSignal(DEFAULT_CONFIG.includeNonTextFiles);
  const [nonTextFilePlaceholder, setNonTextFilePlaceholder] = createSignal(DEFAULT_CONFIG.nonTextFilePlaceholder);
  const [fileTemplate, setFileTemplate] = createSignal(DEFAULT_CONFIG.fileTemplate);
  const [fileSeparator, setFileSeparator] = createSignal(DEFAULT_CONFIG.fileSeparator);
  const [ignoreDirs, setIgnoreDirs] = createSignal([...DEFAULT_CONFIG.ignoreDirs]);
  const [ignorePatterns, setIgnorePatterns] = createSignal([...DEFAULT_CONFIG.ignorePatterns]);
  const [obscuredWords, setObscuredWords] = createSignal({...DEFAULT_CONFIG.obscuredWords});
  
  const [logMessages, setLogMessages] = createSignal([]);
  const [downloadLinks, setDownloadLinks] = createSignal([]); // Stores { href, download }

  // Modal Open States
  const [isTemplateModalOpen, setIsTemplateModalOpen] = createSignal(false);
  const [isSeparatorModalOpen, setIsSeparatorModalOpen] = createSignal(false);
  const [isIgnoreDirsModalOpen, setIsIgnoreDirsModalOpen] = createSignal(false);
  const [isIgnorePatternsModalOpen, setIsIgnorePatternsModalOpen] = createSignal(false);
  const [isObscurationModalOpen, setIsObscurationModalOpen] = createSignal(false);

  // 2. Default Configuration and LocalStorage
  const loadConfig = () => {
    addLogMessage("Attempting to load configuration from localStorage...");
    try {
      const savedConfig = localStorage.getItem(LOCAL_STORAGE_KEY);
      if (savedConfig) {
        const parsed = JSON.parse(savedConfig);
        setMaxTokens(parsed.maxTokens ?? DEFAULT_CONFIG.maxTokens);
        setIncludeNonTextFiles(parsed.includeNonTextFiles ?? DEFAULT_CONFIG.includeNonTextFiles);
        setNonTextFilePlaceholder(parsed.nonTextFilePlaceholder ?? DEFAULT_CONFIG.nonTextFilePlaceholder);
        setFileTemplate(parsed.fileTemplate ?? DEFAULT_CONFIG.fileTemplate);
        setFileSeparator(parsed.fileSeparator ?? DEFAULT_CONFIG.fileSeparator);
        setIgnoreDirs(Array.isArray(parsed.ignoreDirs) ? [...parsed.ignoreDirs] : [...DEFAULT_CONFIG.ignoreDirs]);
        setIgnorePatterns(Array.isArray(parsed.ignorePatterns) ? [...parsed.ignorePatterns] : [...DEFAULT_CONFIG.ignorePatterns]);
        setObscuredWords(typeof parsed.obscuredWords === 'object' && parsed.obscuredWords !== null ? {...parsed.obscuredWords} : {...DEFAULT_CONFIG.obscuredWords});
        addLogMessage("Configuration loaded from localStorage.");
      } else {
        addLogMessage("No saved configuration found, using defaults.");
        // Signals are already initialized with defaults, so no need to set them again here.
      }
    } catch (error) {
      console.error("Failed to load config from localStorage:", error);
      addLogMessage(`Error loading configuration: ${error.message}. Using defaults.`);
      // Ensure defaults are set if parsing fails (though signals are already default initialized)
    }
  };

  const saveConfig = () => {
    const currentConfig = {
      maxTokens: maxTokens(),
      includeNonTextFiles: includeNonTextFiles(),
      nonTextFilePlaceholder: nonTextFilePlaceholder(),
      fileTemplate: fileTemplate(),
      fileSeparator: fileSeparator(),
      ignoreDirs: [...ignoreDirs()],
      ignorePatterns: [...ignorePatterns()],
      obscuredWords: {...obscuredWords()},
    };
    try {
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(currentConfig));
      addLogMessage("Configuration saved to localStorage.");
    } catch (error) {
      console.error("Failed to save config to localStorage:", error);
      addLogMessage(`Error saving configuration: ${error.message}`);
    }
  };

  // Web Worker
  let worker;

  onMount(() => {
    loadConfig(); // Load config first

    // Initialize Web Worker
    worker = new Worker(new URL('./workers/processingWorker.js', import.meta.url), { type: 'module' });
    addLogMessage("Processing worker initialized.");

    worker.onmessage = (event) => {
      const { type, message, file, totalFiles, output_chunks, summary } = event.data;
      switch (type) {
        case 'log':
          addLogMessage(`Worker: ${message}`);
          break;
        case 'progress':
          addLogMessage(`Processing file ${file} (${summary?.processedFiles + 1}/${summary?.totalFiles})...`);
          break;
        case 'error':
          addLogMessage(`Worker Error: ${message}`);
          setIsProcessing(false); // Re-enable UI on error
          break;
        case 'result':
          addLogMessage("Processing complete. Generating download links...");
          handleProcessingResult(output_chunks, summary);
          setIsProcessing(false);
          if (summary) {
            addLogMessage(`Summary: ${summary.totalFilesProcessed} files processed. ${summary.totalTokensGenerated} tokens. ${summary.outputChunkCount} chunks.`);
          }
          break;
        default:
          addLogMessage(`Unknown message type from worker: ${type}`);
      }
    };

    worker.onerror = (error) => {
        addLogMessage(`Unhandled Worker Error: ${error.message}`);
        console.error("Unhandled Worker Error:", error);
        setIsProcessing(false);
    };
  });

  onCleanup(() => {
    if (worker) {
      worker.terminate();
      addLogMessage("Processing worker terminated.");
    }
  });
  
  // Effect to save config when relevant signals change
  createEffect(() => {
    // This effect will run when any of these signals change AFTER initial setup
    // To avoid saving default config on mount before loading, ensure loadConfig runs first.
    // The onMount should handle initial load. This effect is for subsequent changes.
    maxTokens(); 
    includeNonTextFiles();
    nonTextFilePlaceholder();
    fileTemplate();
    fileSeparator();
    ignoreDirs();
    ignorePatterns();
    obscuredWords();
    
    // Check if onMount has completed (simple way, might need refinement for complex scenarios)
    // This effect runs after initial setup (due to onMount changing signals)
    // and then whenever any of the tracked signals change.
    // This ensures that any change, whether from loading or user interaction, gets saved.
    saveConfig();
  });


  const handleFilesSelected = (files) => {
    setSelectedFiles(files); // files is a FileList object or null
    if (files && files.length > 0) {
      let infoText = "";
      if (files[0].webkitRelativePath) {
        const firstFilePathParts = files[0].webkitRelativePath.split('/');
        if (firstFilePathParts.length > 1) {
          setInputDirName(firstFilePathParts[0]);
          infoText = `Folder: ${firstFilePathParts[0]} (${files.length} files/entries)`;
        } else {
          setInputDirName(""); // No directory structure if single file(s) selected
          infoText = `${files.length} file(s) selected`;
        }
      } else {
        setInputDirName("");
        infoText = `${files.length} file(s) selected`;
      }
      addLogMessage(`Selected: ${infoText}`);
    } else {
      setInputDirName("");
      addLogMessage("File/folder selection cleared.");
    }
  };
  
  const addLogMessage = (message) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogMessages(prev => [`[${timestamp}] ${message}`, ...prev].slice(0, 100));
  };

  const clearLog = () => {
    setLogMessages([]);
    addLogMessage("Log cleared.");
  };

  const handleStartProcessing = async () => {
    addLogMessage("Attempting to start processing...");
    setDownloadLinks([]); // Clear previous download links

    if (!selectedFiles() || selectedFiles().length === 0) {
      addLogMessage("Error: No files or folder selected for processing.");
      return;
    }
    if (maxTokens() <= 0) {
      addLogMessage("Error: Max Tokens must be a positive number.");
      return;
    }
    if (!worker) {
        addLogMessage("Error: Processing worker is not available. Please refresh.");
        return;
    }

    setIsProcessing(true);
    addLogMessage("Gathering configuration and sending to worker...");

    const config = {
      max_tokens: maxTokens(), // Worker expects snake_case
      include_non_text_files: includeNonTextFiles(),
      non_text_file_placeholder: nonTextFilePlaceholder(),
      file_template: fileTemplate(),
      file_separator: fileSeparator(),
      ignore_dirs: ignoreDirs(),
      ignore_patterns: ignorePatterns(),
      obscured_words: obscuredWords(),
    };
    
    try {
      // Convert FileList to an array of File objects for transfer
      const filesArray = Array.from(selectedFiles());
      
      worker.postMessage({
        files: filesArray, 
        config: config
      });
      addLogMessage(`Processing started for ${filesArray.length} files/entries.`);
    } catch (error) {
      addLogMessage(`Error starting processing: ${error.message}`);
      console.error("Error posting to worker:", error);
      setIsProcessing(false);
    }
  };

  const handleProcessingResult = async (output_chunks, summary) => {
    if (!output_chunks || output_chunks.length === 0) {
      addLogMessage("No output was generated from processing.");
      setDownloadLinks([]);
      return;
    }

    const baseFileName = inputDirName() ? inputDirName() : "concatext_output";

    if (output_chunks.length === 1) {
      const blob = new Blob([output_chunks[0]], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      setDownloadLinks([{ name: `${baseFileName}_chunk_1.txt`, url: url }]);
      addLogMessage(`Single output chunk generated: ${baseFileName}_chunk_1.txt`);
    } else {
      addLogMessage(`Generating ZIP file for ${output_chunks.length} chunks...`);
      try {
        const zip = new JSZip();
        output_chunks.forEach((chunk, index) => {
          zip.file(`${baseFileName}_chunk_${index + 1}.txt`, chunk);
        });
        const zipBlob = await zip.generateAsync({ type: "blob" });
        const url = URL.createObjectURL(zipBlob);
        setDownloadLinks([{ name: `${baseFileName}_chunks.zip`, url: url }]);
        addLogMessage(`ZIP file generated: ${baseFileName}_chunks.zip`);
      } catch (error) {
        addLogMessage(`Error generating ZIP file: ${error.message}`);
        console.error("ZIP generation error:", error);
        setDownloadLinks([]); // Clear links on error
      }
    }
  };


  return (
    <div class={styles.app}>
      <header class={styles.header}>
        <h1>Concatext Solid.JS</h1>
      </header>
      <main class={styles.mainContainer}>
        {/* Left Column: Configuration Panel */}
        <fieldset class={styles.configPanel} disabled={isProcessing()}>
          <legend class={styles.fieldsetLegend}>Configuration</legend>
          
          <FileInput onFilesSelected={handleFilesSelected} />

          <div class={styles.configItem}>
            <label for="maxTokens">Max Tokens per Chunk:</label>
            <input
              type="number"
              id="maxTokens"
              value={maxTokens()}
              onInput={(e) => setMaxTokens(parseInt(e.target.value, 10) || 0)}
            />
          </div>

          <div class={styles.configItem}>
            <label for="includeNonTextFiles" class={styles.checkboxLabel}>
              <input
                type="checkbox"
                id="includeNonTextFiles"
                checked={includeNonTextFiles()}
                onChange={(e) => setIncludeNonTextFiles(e.target.checked)}
              />
              Include Non-Text Files
            </label>
          </div>

          <Show when={includeNonTextFiles()}>
            <div class={styles.configItem}>
              <label for="nonTextPlaceholder">Non-Text File Placeholder:</label>
              <input
                type="text"
                id="nonTextPlaceholder"
                value={nonTextPlaceholder()}
                onInput={(e) => setNonTextPlaceholder(e.target.value)}
              />
            </div>
          </Show>

          <div class={styles.configSectionTitle}>Advanced Formatting:</div>
          <button class={styles.configButton} onClick={() => setIsTemplateModalOpen(true)}>Edit File Template</button>
          <button class={styles.configButton} onClick={() => setIsSeparatorModalOpen(true)}>Edit File Separator</button>
          
          <div class={styles.configSectionTitle}>Filtering & Obscuration:</div>
          <button class={styles.configButton} onClick={() => setIsIgnoreDirsModalOpen(true)}>Edit Ignored Directories</button>
          <button class={styles.configButton} onClick={() => setIsIgnorePatternsModalOpen(true)}>Edit Ignored File Patterns</button>
          <button class={styles.configButton} onClick={() => setIsObscurationModalOpen(true)}>Edit Obscured Words</button>
          
          <button 
            class={styles.actionButton} 
            onClick={handleStartProcessing}
            disabled={isProcessing()}
          >
            {isProcessing() ? "Processing..." : "Start Processing"}
          </button>
        </fieldset>

        {/* Right Column: Log/Progress and Download Area */}
        <div class={styles.outputPanel}>
          <div class={styles.logArea}>
            <h2>Log / Progress <Show when={inputDirName()}>({inputDirName()})</Show></h2>
            <textarea
              class={styles.logTextarea}
              readOnly
              value={logMessages().join('\n')}
              ref={el => { // Auto scroll to bottom
                if (el) el.scrollTop = el.scrollHeight;
              }}
            />
            <button onClick={clearLog} class={styles.clearLogButton}>Clear Log</button>
          </div>

          <div class={styles.downloadArea}>
            <h2>Download Output Chunks</h2>
            <Show when={downloadLinks().length > 0} fallback={<p>No output files generated yet.</p>}>
              <ul class={styles.downloadList}>
                <For each={downloadLinks()}>{(link) => // link is { name, url }
                  <li class={styles.downloadListItem}>
                    <a href={link.url} download={link.name}>{link.name}</a>
                  </li>
                }</For>
              </ul>
            </Show>
          </div>
        </div>
      </main>

      {/* Modals */}
      <TemplateEditorModal
        isOpen={isTemplateModalOpen()}
        onClose={() => setIsTemplateModalOpen(false)}
        initialTemplate={fileTemplate()}
        onSave={(newTemplate) => {
          setFileTemplate(newTemplate);
          setIsTemplateModalOpen(false);
          addLogMessage("File template updated.");
        }}
      />

      <SeparatorEditorModal
        isOpen={isSeparatorModalOpen()}
        onClose={() => setIsSeparatorModalOpen(false)}
        initialSeparator={fileSeparator()}
        onSave={(newSeparator) => {
          setFileSeparator(newSeparator);
          setIsSeparatorModalOpen(false);
          addLogMessage("File separator updated.");
        }}
      />

      <ListEditorModal
        isOpen={isIgnoreDirsModalOpen()}
        onClose={() => setIsIgnoreDirsModalOpen(false)}
        initialItems={ignoreDirs()}
        title="Edit Ignored Directories"
        onSave={(newItems) => {
          setIgnoreDirs(newItems);
          setIsIgnoreDirsModalOpen(false);
          addLogMessage("Ignored directories updated.");
        }}
      />

      <ListEditorModal
        isOpen={isIgnorePatternsModalOpen()}
        onClose={() => setIsIgnorePatternsModalOpen(false)}
        initialItems={ignorePatterns()}
        title="Edit Ignored File Patterns"
        onSave={(newItems) => {
          setIgnorePatterns(newItems);
          setIsIgnorePatternsModalOpen(false);
          addLogMessage("Ignored file patterns updated.");
        }}
      />
      
      <ObscurationEditorModal
        isOpen={isObscurationModalOpen()}
        onClose={() => setIsObscurationModalOpen(false)}
        initialMap={obscuredWords()}
        onSave={(newMap) => {
          setObscuredWords(newMap);
          setIsObscurationModalOpen(false);
          addLogMessage("Obscured words map updated.");
        }}
      />
    </div>
  );
}

export default App;
