import { Label, Toast } from "radix-ui";
import { useId, useRef, useState } from "react";
import { ApiError, uploadDocuments } from "../api/client";

const ALLOWED_EXTENSIONS = [".pdf", ".txt", ".md"];

type UploadStatus = "idle" | "uploading";
type ToastState =
  | { open: false }
  | { open: true; kind: "success"; title: string; description: string }
  | { open: true; kind: "error"; title: string; description: string };

function hasAllowedExtension(filename: string): boolean {
  const lower = filename.toLowerCase();
  return ALLOWED_EXTENSIONS.some((extension) => lower.endsWith(extension));
}

function DocumentUpload() {
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [toast, setToast] = useState<ToastState>({ open: false });
  const inputRef = useRef<HTMLInputElement>(null);
  const inputId = useId();

  async function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    if (files.length === 0) return;

    const rejected = files.filter((file) => !hasAllowedExtension(file.name));
    if (rejected.length > 0) {
      setToast({
        open: true,
        kind: "error",
        title: "Unsupported file",
        description: `Only ${ALLOWED_EXTENSIONS.join(", ")} files are supported. Rejected: ${rejected.map((f) => f.name).join(", ")}.`,
      });
      if (inputRef.current) inputRef.current.value = "";
      return;
    }

    setStatus("uploading");

    try {
      const results = await uploadDocuments(files);
      const summary = results.map((r) => `"${r.filename}" (${r.chunks_indexed} chunks)`).join(", ");
      setToast({
        open: true,
        kind: "success",
        title: results.length === 1 ? "Document indexed" : "Documents indexed",
        description: summary,
      });
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "Upload failed. Please try again.";
      setToast({ open: true, kind: "error", title: "Upload failed", description: message });
    } finally {
      setStatus("idle");
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <Toast.Provider swipeDirection="right">
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/60 dark:border-slate-800 dark:bg-slate-900 dark:shadow-none">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
          Upload documents
        </h2>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          PDF, TXT, or MD. They will be split, embedded, and indexed for chat.
        </p>

        <div className="mt-4">
          <Label.Root htmlFor={inputId} className="sr-only">
            Choose one or more documents
          </Label.Root>
          <label
            htmlFor={inputId}
            className="flex cursor-pointer items-center justify-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 px-4 py-8 text-sm text-slate-500 transition-colors hover:border-indigo-400 hover:bg-indigo-50/50 hover:text-indigo-600 aria-disabled:cursor-not-allowed aria-disabled:opacity-60 dark:border-slate-700 dark:bg-slate-950/40 dark:text-slate-400 dark:hover:border-indigo-500 dark:hover:bg-indigo-500/10 dark:hover:text-indigo-400"
            aria-disabled={status === "uploading"}
          >
            {status === "uploading" ? "Uploading and indexing..." : "Click to choose files, or drag them here"}
          </label>
          <input
            ref={inputRef}
            id={inputId}
            type="file"
            accept=".pdf,.txt,.md,application/pdf,text/plain,text/markdown"
            multiple
            onChange={handleFileChange}
            disabled={status === "uploading"}
            className="sr-only"
          />
        </div>
      </section>

      {toast.open && (
        <Toast.Root
          className={`rounded-xl border p-4 shadow-lg transition-all data-[state=closed]:opacity-0 ${
            toast.kind === "success"
              ? "border-emerald-200 bg-emerald-50 dark:border-emerald-900 dark:bg-emerald-950"
              : "border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950"
          }`}
          open={toast.open}
          onOpenChange={(open) => !open && setToast({ open: false })}
          duration={4000}
        >
          <Toast.Title
            className={`text-sm font-semibold ${
              toast.kind === "success"
                ? "text-emerald-900 dark:text-emerald-100"
                : "text-red-900 dark:text-red-100"
            }`}
          >
            {toast.title}
          </Toast.Title>
          <Toast.Description
            className={`mt-1 text-sm ${
              toast.kind === "success"
                ? "text-emerald-700 dark:text-emerald-300"
                : "text-red-700 dark:text-red-300"
            }`}
          >
            {toast.description}
          </Toast.Description>
        </Toast.Root>
      )}
      <Toast.Viewport className="fixed bottom-4 right-4 z-50 flex w-80 flex-col gap-2 outline-none" />
    </Toast.Provider>
  );
}

export default DocumentUpload;
