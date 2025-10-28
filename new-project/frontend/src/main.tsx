import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';

const API_BASE = (import.meta as any)?.env?.VITE_API_BASE || 'http://localhost:3000';

function App() {
  const [health, setHealth] = useState<string>('unknown');
  const [triageResult, setTriageResult] = useState<any>(null);
  const [kbQuery, setKbQuery] = useState<string>('');
  const [kbResults, setKbResults] = useState<any[]>([]);

  useEffect(() => {
    fetch(`${API_BASE}/api/health`)
      .then((r) => r.json())
      .then((j) => setHealth(JSON.stringify(j)))
      .catch((e) => setHealth('error'));
  }, []);

  const runTriage = async () => {
    const res = await fetch(`${API_BASE}/api/triage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ alertId: 'sample-alert-1' }),
    });
    const json = await res.json();
    setTriageResult(json);
  };

  const searchKb = async () => {
    const q = encodeURIComponent(kbQuery);
    const res = await fetch(`${API_BASE}/api/kb/search?q=${q}`);
    const json = await res.json();
    setKbResults(json.results || []);
  };

  return (
    <div style={{ padding: 24, fontFamily: 'sans-serif' }}>
      <h1>Case Resolution Console (scaffold)</h1>

      <section style={{ marginTop: 16 }}>
        <strong>Backend health:</strong>
        <pre>{health}</pre>
      </section>

      <section style={{ marginTop: 16 }}>
        <button onClick={runTriage}>Start sample triage</button>
        <pre>{triageResult ? JSON.stringify(triageResult, null, 2) : 'no result'}</pre>
      </section>

      <section style={{ marginTop: 16 }}>
        <div>
          <input value={kbQuery} onChange={(e) => setKbQuery(e.target.value)} placeholder="KB search..." />
          <button onClick={searchKb} style={{ marginLeft: 8 }}>
            Search KB
          </button>
        </div>
        <ul>
          {kbResults.map((r) => (
            <li key={r.docId}>{r.title}: {r.extract}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
