import { useRef, useState } from "react";
import { ApiError, uploadDocument } from "../api/client";

type UploadStatus =
  | { kind: "idle" }
  | { kind: "uploading" }
  | { kind: "success"; filename: string; chunksIndexed: number }
  | { kind: "error"; message: string };

function DocumentUpload() {
  const [status, setStatus] = useState<UploadStatus>({ kind: "idle" });
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setStatus({ kind: "error", message: "Only PDF files are supported." });
      if (inputRef.current) inputRef.current.value = "";
      return;
    }

    setStatus({ kind: "uploading" });

    try {
      const result = await uploadDocument(file);
      setStatus({
        kind: "success",
        filename: result.filename,
        chunksIndexed: result.chunks_indexed,
      });
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "Upload failed. Please try again.";
      setStatus({ kind: "error", message });
    } finally {
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <section>
      <h2>Upload a document</h2>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        onChange={handleFileChange}
        disabled={status.kind === "uploading"}
      />

      {status.kind === "uploading" && <p>Uploading and indexing document...</p>}
      {status.kind === "success" && (
        <p>
          "{status.filename}" indexed successfully ({status.chunksIndexed} chunks).
        </p>
      )}
      {status.kind === "error" && <p role="alert">{status.message}</p>}
    </section>
  );
}

export default DocumentUpload;
