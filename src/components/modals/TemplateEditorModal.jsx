// src/components/modals/TemplateEditorModal.jsx
import { createSignal, onMount, Show } from 'solid-js';
import ModalBase from './ModalBase';
// No specific styles needed if ModalBase.module.css covers general input/textarea

function TemplateEditorModal(props) {
  const [template, setTemplate] = createSignal("");

  // Use onMount or a createEffect to update local state when initialTemplate changes
  onMount(() => {
    if (props.initialTemplate !== undefined) {
      setTemplate(props.initialTemplate);
    }
  });

  // If the modal can be re-opened with different initial values while mounted,
  // an effect is better:
  // createEffect(() => {
  //   if (props.isOpen() && props.initialTemplate !== undefined) {
  //     setTemplate(props.initialTemplate);
  //   }
  // });

  const handleSave = () => {
    if (props.onSave) {
      props.onSave(template());
    }
    props.onClose();
  };

  return (
    <ModalBase
      isOpen={props.isOpen}
      onClose={props.onClose}
      onSave={handleSave}
      title="Edit File Template"
      saveLabel="Save Template"
    >
      <div>
        <p>Define the template for each file's content. Use these placeholders:</p>
        <ul>
          <li><code>{'{path}'}</code> - The relative path of the file.</li>
          <li><code>{'{name}'}</code> - The name of the file.</li>
          <li><code>{'{content}'}</code> - The actual content of the file.</li>
        </ul>
        <textarea
          value={template()}
          onInput={(e) => setTemplate(e.target.value)}
          rows="5"
          placeholder="Example: File: {name}\nPath: {path}\n\n{content}"
          style={{ "width": "100%", "min-height": "100px" }} // Inline style for quick setup
        />
      </div>
    </ModalBase>
  );
}

export default TemplateEditorModal;
