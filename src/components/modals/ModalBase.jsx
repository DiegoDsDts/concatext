// src/components/modals/ModalBase.jsx
import { Show } from 'solid-js';
import styles from './ModalBase.module.css';

function ModalBase(props) {
  const handleOverlayClick = (event) => {
    // Close only if the overlay itself is clicked, not content within it
    if (event.target === event.currentTarget) {
      props.onClose();
    }
  };

  return (
    <Show when={props.isOpen()}>
      <div class={styles.modalOverlay} onClick={handleOverlayClick}>
        <div class={styles.modalContent}>
          <h2 class={styles.modalTitle}>{props.title}</h2>
          <div class={styles.modalBody}>
            {props.children}
          </div>
          <div class={styles.modalActions}>
            <Show when={props.onSave}>
              <button onClick={props.onSave} class={`${styles.modalButton} ${styles.saveButton}`}>
                {props.saveLabel || "Save"}
              </button>
            </Show>
            <button onClick={props.onClose} class={`${styles.modalButton} ${styles.cancelButton}`}>
              {props.cancelLabel || "Cancel"}
            </button>
          </div>
        </div>
      </div>
    </Show>
  );
}

export default ModalBase;
