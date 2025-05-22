// src/components/modals/ListEditorModal.jsx
import { createSignal, For, onMount } from 'solid-js';
import ModalBase from './ModalBase';
import styles from './ListEditorModal.module.css'; // Create this if specific styles are needed

function ListEditorModal(props) {
  const [items, setItems] = createSignal([]);
  const [newItem, setNewItem] = createSignal("");

  // Initialize items from props
  onMount(() => {
    if (props.initialItems) {
      setItems([...props.initialItems]);
    }
  });

  // If the modal can be re-opened with different initial values while mounted,
  // an effect might be better for props.initialItems:
  // createEffect(() => {
  //   if (props.isOpen() && props.initialItems) {
  //     setItems([...props.initialItems]);
  //   } else if (!props.isOpen()) {
  //      // Optional: clear state when closed if desired, or rely on onMount next time
  //   }
  // });

  const handleAddItem = () => {
    const trimmedItem = newItem().trim();
    if (trimmedItem && !items().includes(trimmedItem)) {
      setItems([...items(), trimmedItem]);
      setNewItem(""); // Clear input
    } else if (items().includes(trimmedItem)) {
      // Optionally, provide feedback that item already exists
      console.warn("Item already in list:", trimmedItem);
    }
  };

  const handleRemoveItem = (itemToRemove) => {
    setItems(items().filter(item => item !== itemToRemove));
  };

  const handleSave = () => {
    if (props.onSave) {
      props.onSave([...items()]); // Pass a copy of the array
    }
    props.onClose();
  };

  return (
    <ModalBase
      isOpen={props.isOpen}
      onClose={props.onClose}
      onSave={handleSave}
      title={props.title || "Edit List"}
      saveLabel="Save List"
    >
      <div class={styles.listEditorContainer}>
        <div class={styles.addItemControls}>
          <input
            type="text"
            value={newItem()}
            onInput={(e) => setNewItem(e.target.value)}
            placeholder="Enter new item..."
            class={styles.addItemInput}
            onKeyPress={(e) => { if (e.key === 'Enter') handleAddItem(); }}
          />
          <button onClick={handleAddItem} class={styles.addButton}>Add</button>
        </div>
        <Show when={items().length > 0} fallback={<p class={styles.emptyListMessage}>No items in the list.</p>}>
          <ul class={styles.itemList}>
            <For each={items()}>{(item, index) =>
              <li class={styles.itemEntry}>
                <span class={styles.itemText}>{item}</span>
                <button onClick={() => handleRemoveItem(item)} class={styles.removeButton}>
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

export default ListEditorModal;
