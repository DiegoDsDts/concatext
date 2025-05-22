// src/components/modals/SeparatorEditorModal.jsx
import { createSignal, onMount } from 'solid-js';
import ModalBase from './ModalBase';

function SeparatorEditorModal(props) {
  const [separator, setSeparator] = createSignal("");

  onMount(() => {
    if (props.initialSeparator !== undefined) {
      setSeparator(props.initialSeparator);
    }
  });

  // createEffect(() => {
  //   if (props.isOpen() && props.initialSeparator !== undefined) {
  //     setSeparator(props.initialSeparator);
  //   }
  // });

  const handleSave = () => {
    if (props.onSave) {
      props.onSave(separator());
    }
    props.onClose();
  };

  return (
    <ModalBase
      isOpen={props.isOpen}
      onClose={props.onClose}
      onSave={handleSave}
      title="Edit File Separator"
      saveLabel="Save Separator"
    >
      <div>
        <p>Enter text to insert between concatenated files. Use <code>\\n</code> for new lines (it will be interpreted as a newline character).</p>
        <textarea
          value={separator()}
          onInput={(e) => setSeparator(e.target.value)}
          rows="3"
          placeholder="Example: \n---\n"
          style={{ "width": "100%", "min-height": "80px" }}
        />
        <p style={{"font-size":"0.8em", "color":"gray"}}>
          For example, to add a horizontal rule and two newlines, you might enter:
          <code>\n\n--------------------\n\n</code>
        </p>
      </div>
    </ModalBase>
  );
}

export default SeparatorEditorModal;
