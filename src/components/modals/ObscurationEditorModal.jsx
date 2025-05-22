// src/components/modals/ObscurationEditorModal.jsx
import { createSignal, For, onMount, createEffect } from 'solid-js';
import ModalBase from './ModalBase';
import styles from './ObscurationEditorModal.module.css'; // Create this for specific styles

function ObscurationEditorModal(props) {
  const [mappings, setMappings] = createSignal({});
  const [originalWord, setOriginalWord] = createSignal("");
  const [placeholder, setPlaceholder] = createSignal("");

  // Initialize mappings from props
  onMount(() => {
    if (props.initialMap) {
      setMappings({...props.initialMap});
    }
  });

  // If the modal can be re-opened with different initial values while mounted
  createEffect(() => {
    if (props.isOpen() && props.initialMap) {
      setMappings({...props.initialMap});
    } else if (!props.isOpen()) {
      // Optional: clear state when closed if desired
      // setOriginalWord("");
      // setPlaceholder("");
      // setMappings({}); // Or reset to initialMap if you want it to "reset" on each open
    }
  });

  const handleAddOrUpdateMapping = () => {
    const word = originalWord().trim();
    const ph = placeholder().trim();
    if (word && ph) {
      setMappings(prev => ({ ...prev, [word]: ph }));
      setOriginalWord("");
      setPlaceholder("");
    } else {
      // Optional: feedback if fields are empty
      console.warn("Original word and placeholder cannot be empty.");
    }
  };

  const handleRemoveMapping = (wordToRemove) => {
    const { [wordToRemove]: _, ...remainingMappings } = mappings();
    setMappings(remainingMappings);
  };

  const handleSave = () => {
    if (props.onSave) {
      props.onSave({...mappings()}); // Pass a copy of the map
    }
    props.onClose();
  };

  return (
    <ModalBase
      isOpen={props.isOpen}
      onClose={props.onClose}
      onSave={handleSave}
      title="Edit Text Obscuration Map"
      saveLabel="Save Mappings"
    >
      <div class={styles.obscurationEditorContainer}>
        <div class={styles.addMappingControls}>
          <input
            type="text"
            value={originalWord()}
            onInput={(e) => setOriginalWord(e.target.value)}
            placeholder="Original Text (word)"
            class={styles.mappingInput}
          />
          <input
            type="text"
            value={placeholder()}
            onInput={(e) => setPlaceholder(e.target.value)}
            placeholder="Placeholder (e.g., XXXX)"
            class={styles.mappingInput}
          />
          <button onClick={handleAddOrUpdateMapping} class={styles.addButton}>
            Add/Update Mapping
          </button>
        </div>

        <Show
          when={Object.keys(mappings()).length > 0}
          fallback={<p class={styles.emptyMappingsMessage}>No mappings defined.</p>}
        >
          <ul class={styles.mappingsList}>
            <For each={Object.entries(mappings())}>{([word, ph]) =>
              <li class={styles.mappingEntry}>
                <span class={styles.mappingText}>
                  <code>{word}</code> &rarr; <code>{ph}</code>
                </span>
                <button onClick={() => handleRemoveMapping(word)} class={styles.removeButton}>
                  Remove
                </button>
              </li>
            }</For>
          </ul>
        </Show>
      </div>
    </ModalBase>
  );
}

export default ObscurationEditorModal;
