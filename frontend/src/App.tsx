import { useEffect, useState } from "react";
import { checkHealth } from "./api/client";
import Chat from "./components/Chat";
import DocumentUpload from "./components/DocumentUpload";

type BackendStatus = "checking" | "online" | "offline";

const statusStyles: Record<BackendStatus, string> = {
  checking: "bg-amber-400",
  online: "bg-emerald-500",
  offline: "bg-red-500",
};

function App() {
  const [status, setStatus] = useState<BackendStatus>("checking");

  useEffect(() => {
    checkHealth().then((ok) => setStatus(ok ? "online" : "offline"));
  }, []);

  return (
    <div className="min-h-svh">
      <main className="mx-auto flex max-w-2xl flex-col gap-8 px-6 py-16">
        <header className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-semibold tracking-tight text-slate-900 dark:text-white">
              Document Assistant
            </h1>
            <span
              className={`inline-block h-2.5 w-2.5 rounded-full ${statusStyles[status]}`}
              title={`Backend: ${status}`}
            />
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Upload a PDF, then chat about its content.
          </p>
        </header>

        <DocumentUpload />

        <Chat />
      </main>
    </div>
  );
}

export default App;
