"use client";

import { useMemo, useState } from "react";
import { FileUploader } from "@/components/file-uploader";
import type { OCRFields, OCRResponse } from "@/lib/types";
import styles from "./page.module.css";

const API_BASE = process.env.NEXT_PUBLIC_OCR_API ?? "http://localhost:8000";

const DOC_TYPES = [
  { value: "ine", label: "Credencial INE" },
  { value: "curp", label: "Constancia CURP" },
] as const;

export default function Home() {
  const [documentType, setDocumentType] = useState<(typeof DOC_TYPES)[number]["value"]>("ine");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fields, setFields] = useState<OCRFields | null>(null);
  const [metadata, setMetadata] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const hasResult = useMemo(() => Boolean(fields), [fields]);

  const handleSubmit = async (evt: React.FormEvent<HTMLFormElement>) => {
    evt.preventDefault();
    if (!selectedFile) {
      setError("Selecciona un archivo antes de analizar.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setFields(null);
    setMetadata(null);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch(`${API_BASE}/ocr?document_type=${documentType}`, {
        method: "POST",
        body: formData,
      });

      const payload = await response.json();

      if (!response.ok) {
        const detail = (payload as { detail?: string }).detail;
        throw new Error(detail ?? "La API respondió con un error");
      }

      const data = payload as OCRResponse;
      setFields(data.fields);
      setMetadata(data.metadata);
    } catch (fetchError) {
      const message =
        fetchError instanceof Error
          ? fetchError.message
          : "Error inesperado al contactar la API";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const resetState = () => {
    setSelectedFile(null);
    setFields(null);
    setMetadata(null);
    setError(null);
  };

  return (
    <div className={styles.page}>
      <main className={styles.shell}>
        <section className={styles.panel}>
          <div className={styles.header}>
            <span className={styles.badge}>OCR demo</span>
            <h1>Extrae datos clave de INE o CURP en segundos</h1>
            <p>
              Carga un PDF o imagen y consulta el JSON. Para INE extrae Nombre, Domicilio, CURP y fechas; para CURP
              extrae Nombre, Clave y estado de certificación.
            </p>
          </div>

          <form className={styles.form} onSubmit={handleSubmit}>
            <label className={styles.label}>
              Tipo de documento
              <select
                value={documentType}
                onChange={(evt) => setDocumentType(evt.target.value as (typeof DOC_TYPES)[number]["value"])}
                disabled={isLoading}
                className={styles.input}
              >
                {DOC_TYPES.map((option) => (
                  <option value={option.value} key={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <FileUploader disabled={isLoading} onFileAccepted={setSelectedFile} />

            <div className={styles.actions}>
              <button
                type="submit"
                className={styles.button}
                disabled={isLoading || !selectedFile}
              >
                {isLoading ? "Procesando..." : "Analizar documento"}
              </button>
              <button
                type="button"
                className={`${styles.button} ${styles.secondaryButton}`}
                onClick={resetState}
                disabled={isLoading}
              >
                Limpiar
              </button>
            </div>

            {error && <p className={styles.error}>{error}</p>}
            {!error && !selectedFile && (
              <p className={styles.hint}>Tip: usa los archivos en la carpeta test_material/ para hacer una prueba rápida.</p>
            )}
          </form>
        </section>

        <section className={`${styles.panel} ${styles.results}`}>
          <div className={styles.resultsHeader}>
            <h2>Respuesta de la API</h2>
            {metadata && (
              <span className={styles.metaBadge}>
                {metadata.pages ? `${metadata.pages} página(s)` : "Sin info"}
              </span>
            )}
          </div>

          {hasResult ? (
            <>
              {documentType === "curp" ? (
                <dl className={styles.grid}>
                  <div>
                    <dt>Nombre</dt>
                    <dd>{fields?.name ?? "No detectado"}</dd>
                  </div>
                  <div>
                    <dt>Clave</dt>
                    <dd>{fields?.clave ?? fields?.curp ?? "No detectado"}</dd>
                  </div>
                  <div>
                    <dt>Certificación</dt>
                    <dd>
                      {fields?.certification_status ??
                        (fields?.is_certified ? "CURP Certificada" : "No detectado")}
                    </dd>
                  </div>
                </dl>
              ) : (
                <dl className={styles.grid}>
                  <div>
                    <dt>Nombre</dt>
                    <dd>{fields?.name ?? "No detectado"}</dd>
                  </div>
                  <div>
                    <dt>Domicilio</dt>
                    <dd>{fields?.address ?? "No detectado"}</dd>
                  </div>
                  <div>
                    <dt>CURP</dt>
                    <dd>{fields?.curp ?? "No detectado"}</dd>
                  </div>
                  <div>
                    <dt>Fecha de nacimiento</dt>
                    <dd>{fields?.birth_date ?? "No detectado"}</dd>
                  </div>
                  <div>
                    <dt>Vigencia</dt>
                    <dd>{fields?.validity ?? "No detectado"}</dd>
                  </div>
                </dl>
              )}
              <label className={styles.label}>
                Texto completo OCR
                <textarea
                  readOnly
                  className={`${styles.input} ${styles.textarea}`}
                  value={fields?.full_text ?? ""}
                />
              </label>
            </>
          ) : (
            <p className={styles.placeholder}>
              Aquí verás el JSON una vez que proceses un archivo. Ideal para validar que tu backend FastAPI está corriendo.
            </p>
          )}
        </section>
      </main>
    </div>
  );
}
