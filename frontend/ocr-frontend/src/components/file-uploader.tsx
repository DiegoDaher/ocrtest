"use client";

import { useCallback, useRef, useState } from "react";

const ACCEPTED_TYPES = [
  "application/pdf",
  "image/jpeg",
  "image/png",
  "image/webp",
];

interface FileUploaderProps {
  disabled?: boolean;
  onFileAccepted: (file: File) => void;
}

export function FileUploader({ disabled, onFileAccepted }: FileUploaderProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [fileName, setFileName] = useState<string>("");

  const openFileDialog = () => {
    inputRef.current?.click();
  };

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return;
      const file = files[0];
      if (ACCEPTED_TYPES.includes(file.type)) {
        setFileName(file.name);
        onFileAccepted(file);
      } else {
        alert("Formato no soportado. Usa PDF, JPG o PNG.");
      }
    },
    [onFileAccepted]
  );

  const onDrop = (evt: React.DragEvent<HTMLDivElement>) => {
    evt.preventDefault();
    if (disabled) return;
    setDragActive(false);
    handleFiles(evt.dataTransfer.files);
  };

  return (
    <div
      className={`dropzone ${dragActive ? "dropzone--active" : ""}`}
      onDragOver={(evt) => {
        evt.preventDefault();
        if (!disabled) setDragActive(true);
      }}
      onDragLeave={() => setDragActive(false)}
      onDrop={onDrop}
      onClick={() => !disabled && openFileDialog()}
      aria-disabled={disabled}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_TYPES.join(",")}
        className="dropzone__input"
        onChange={(evt) => handleFiles(evt.target.files)}
        disabled={disabled}
      />
      <p className="dropzone__title">
        Arrastra tu archivo o haz clic para explorar
      </p>
      <p className="dropzone__hint">
        Se permiten PDF, JPG, PNG o WebP (máx. 10 MB)
      </p>
      {fileName && <p className="dropzone__file">Seleccionado: {fileName}</p>}
    </div>
  );
}
