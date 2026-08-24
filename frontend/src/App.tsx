import { useEffect, useState } from "react";
import { checkHealth } from "./api/client";
import DocumentUpload from "./components/DocumentUpload";
import "./App.css";

type BackendStatus = "checking" | "online" | "offline";

function App() {
  const [status, setStatus] = useState<BackendStatus>("checking");

  useEffect(() => {
    checkHealth().then((ok) => setStatus(ok ? "online" : "offline"));
  }, []);

  return (
    <main>
      <h1>Document Assistant</h1>
      <p>
        Backend: <strong>{status}</strong>
      </p>

      <DocumentUpload />

      <p>Chat page coming next (DA-25).</p>
    </main>
  );
}

export default App;
