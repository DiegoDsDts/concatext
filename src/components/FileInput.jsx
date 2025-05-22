// src/components/FileInput.jsx
import { createSignal } from "solid-js";
import styles from './FileInput.module.css'; // We'll create this CSS file later

function FileInput(props) {
  const [fileInfo, setFileInfo] = createSignal("No folder selected");

  const handleFileChange = (event) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      // For a directory, files[0].webkitRelativePath will show the directory path
      // For multiple files, it's just a list.
      // We can display the name of the first file's directory or count of files.
      if (files[0].webkitRelativePath) {
        const firstFilePathParts = files[0].webkitRelativePath.split('/');
        if (firstFilePathParts.length > 1) {
          setFileInfo(`Folder: ${firstFilePathParts[0]} (${files.length} files)`);
        } else {
          setFileInfo(`${files.length} file(s) selected`);
        }
      } else {
        setFileInfo(`${files.length} file(s) selected`);
      }
      if (props.onFilesSelected) {
        props.onFilesSelected(files);
      }
    } else {
      setFileInfo("No folder selected");
      if (props.onFilesSelected) {
        props.onFilesSelected(null);
      }
    }
  };

  return (
    <div class={styles.fileInputContainer}>
      <label for="file-upload" class={styles.fileUploadLabel}>
        Select Folder
      </label>
      <input
        type="file"
        id="file-upload"
        webkitdirectory
        directory
        multiple
        onChange={handleFileChange}
        class={styles.fileUploadInput}
      />
      <div class={styles.fileInfoDisplay}>{fileInfo()}</div>
    </div>
  );
}

export default FileInput;
