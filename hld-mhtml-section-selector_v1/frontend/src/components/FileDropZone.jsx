import { useRef, useState } from "react";

export default function FileDropZone({ disabled, onFileSelected }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const acceptFile = (file) => {
    if (!file) return;
    onFileSelected(file);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <section
      className={`drop-zone ${dragging ? "drop-zone--active" : ""}`}
      onDragEnter={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDragOver={(event) => event.preventDefault()}
      onDragLeave={(event) => {
        event.preventDefault();
        if (event.currentTarget === event.target) setDragging(false);
      }}
      onDrop={(event) => {
        event.preventDefault();
        setDragging(false);
        acceptFile(event.dataTransfer.files?.[0]);
      }}
      aria-label="Upload an HLD MHTML file"
    >
      <div className="upload-icon" aria-hidden="true">⇧</div>
      <h2>Upload HLD document</h2>
      <p>Drop a Word or browser-exported MHTML file here, or browse from the computer.</p>
      <button
        type="button"
        className="button button--primary"
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
      >
        Browse for MHTML
      </button>
      <input
        ref={inputRef}
        className="visually-hidden"
        type="file"
        accept=".mhtml,.mht,message/rfc822,multipart/related"
        disabled={disabled}
        onChange={(event) => acceptFile(event.target.files?.[0])}
      />
      <small>Supported: .mhtml and .mht, maximum 25 MB</small>
    </section>
  );
}
