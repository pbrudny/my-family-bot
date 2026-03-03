import { useState, useEffect } from "react";

const S: Record<string, React.CSSProperties> = {
  page:       { minHeight: "100vh", background: "#f5f5f5" },
  header:     { background: "#2563eb", color: "#fff", padding: "1rem 2rem", display: "flex", alignItems: "center", gap: "1rem" },
  title:      { margin: 0, fontSize: "1.25rem", fontWeight: 700, flex: 1 },
  backBtn:    { background: "rgba(255,255,255,0.2)", border: "none", color: "#fff", padding: "0.4rem 0.9rem", borderRadius: 6, cursor: "pointer", fontSize: "0.9rem" },
  body:       { maxWidth: 760, margin: "0 auto", padding: "2rem 1rem", display: "flex", flexDirection: "column", gap: "1.5rem" },
  card:       { background: "#fff", borderRadius: 10, boxShadow: "0 1px 8px rgba(0,0,0,0.08)", padding: "1.5rem" },
  cardTitle:  { margin: "0 0 1rem", fontSize: "1rem", fontWeight: 700, color: "#111" },
  label:      { display: "block", fontSize: "0.85rem", fontWeight: 600, marginBottom: "0.35rem" },
  input:      { width: "100%", padding: "0.55rem 0.8rem", border: "1px solid #ddd", borderRadius: 6, fontSize: "0.95rem", boxSizing: "border-box" },
  row:        { display: "flex", gap: "0.75rem", alignItems: "flex-end" },
  btn:        { padding: "0.55rem 1.2rem", background: "#2563eb", color: "#fff", border: "none", borderRadius: 6, fontWeight: 600, cursor: "pointer", fontSize: "0.9rem", whiteSpace: "nowrap" },
  btnDanger:  { padding: "0.55rem 1.2rem", background: "#dc2626", color: "#fff", border: "none", borderRadius: 6, fontWeight: 600, cursor: "pointer", fontSize: "0.9rem" },
  btnSm:      { padding: "0.3rem 0.75rem", background: "#2563eb", color: "#fff", border: "none", borderRadius: 6, fontWeight: 600, cursor: "pointer", fontSize: "0.82rem" },
  msg:        { marginTop: "0.75rem", padding: "0.6rem 0.9rem", borderRadius: 6, fontSize: "0.9rem" },
  ok:         { background: "#dcfce7", color: "#166534" },
  err:        { background: "#fee2e2", color: "#991b1b" },
  fileBox:    { border: "2px dashed #ddd", borderRadius: 8, padding: "1.5rem", textAlign: "center", cursor: "pointer", color: "#666", fontSize: "0.9rem" },
  table:      { width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" },
  th:         { textAlign: "left", padding: "0.5rem 0.75rem", borderBottom: "2px solid #eee", fontWeight: 600, color: "#555" },
  td:         { padding: "0.5rem 0.75rem", borderBottom: "1px solid #f0f0f0", verticalAlign: "middle" },
  badge:      { display: "inline-block", padding: "0.15rem 0.5rem", borderRadius: 999, fontSize: "0.78rem", background: "#dbeafe", color: "#1e40af" },
  empty:      { color: "#999", textAlign: "center", padding: "1.5rem 0", fontSize: "0.9rem" },
  mb:         { marginBottom: "0.75rem" },
};

interface Person { id: string; name: string; whatsapp?: string }

export default function Admin() {
  const [apiKey, setApiKey]       = useState(() => localStorage.getItem("adminKey") ?? "");
  const [saved, setSaved]         = useState(!!localStorage.getItem("adminKey"));
  const [persons, setPersons]     = useState<Person[]>([]);
  const [loadingP, setLoadingP]   = useState(false);
  const [gedFile, setGedFile]     = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [gedMsg, setGedMsg]       = useState<{ ok: boolean; text: string } | null>(null);
  const [waId, setWaId]           = useState("");
  const [waPhone, setWaPhone]     = useState("");
  const [waMsg, setWaMsg]         = useState<{ ok: boolean; text: string } | null>(null);

  function saveKey() {
    localStorage.setItem("adminKey", apiKey);
    setSaved(true);
  }

  function clearKey() {
    localStorage.removeItem("adminKey");
    setApiKey("");
    setSaved(false);
    setPersons([]);
  }

  async function loadPersons() {
    setLoadingP(true);
    try {
      const res = await fetch("/admin/persons", { headers: { "X-Admin-Key": apiKey } });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data = await res.json();
      setPersons(data.persons ?? data);
    } catch (e: unknown) {
      alert("Failed to load persons: " + (e instanceof Error ? e.message : e));
    } finally {
      setLoadingP(false);
    }
  }

  async function uploadGedcom() {
    if (!gedFile) return;
    setUploading(true);
    setGedMsg(null);
    const form = new FormData();
    form.append("file", gedFile);
    try {
      const res = await fetch("/admin/upload-gedcom", {
        method: "POST",
        headers: { "X-Admin-Key": apiKey },
        body: form,
      });
      const data = await res.json();
      setGedMsg({ ok: res.ok, text: res.ok ? (data.message ?? "Imported successfully.") : (data.detail ?? "Upload failed.") });
      if (res.ok) { setGedFile(null); loadPersons(); }
    } catch (e: unknown) {
      setGedMsg({ ok: false, text: "Network error: " + (e instanceof Error ? e.message : e) });
    } finally {
      setUploading(false);
    }
  }

  async function mapWhatsapp() {
    setWaMsg(null);
    try {
      const res = await fetch("/admin/map-whatsapp", {
        method: "POST",
        headers: { "X-Admin-Key": apiKey, "Content-Type": "application/json" },
        body: JSON.stringify({ person_id: waId, whatsapp_number: waPhone }),
      });
      const data = await res.json();
      setWaMsg({ ok: res.ok, text: res.ok ? "Mapped successfully." : (data.detail ?? "Failed.") });
      if (res.ok) { setWaId(""); setWaPhone(""); loadPersons(); }
    } catch (e: unknown) {
      setWaMsg({ ok: false, text: "Network error: " + (e instanceof Error ? e.message : e) });
    }
  }

  useEffect(() => { if (saved && apiKey) loadPersons(); }, [saved]);

  return (
    <div style={S.page}>
      <header style={S.header}>
        <h1 style={S.title}>Admin</h1>
        <button style={S.backBtn} onClick={() => window.location.href = "/"}>← Back to chat</button>
      </header>

      <div style={S.body}>

        {/* API Key */}
        <div style={S.card}>
          <p style={S.cardTitle}>API Key</p>
          <div style={S.row}>
            <div style={{ flex: 1 }}>
              <input style={S.input} type="password" placeholder="X-Admin-Key"
                value={apiKey} onChange={e => { setApiKey(e.target.value); setSaved(false); }} />
            </div>
            <button style={S.btn} onClick={saveKey}>Save</button>
            {saved && <button style={S.btnDanger} onClick={clearKey}>Clear</button>}
          </div>
          {saved && <p style={{ ...S.msg, ...S.ok }}>Key saved to browser.</p>}
        </div>

        {/* GEDCOM Upload */}
        <div style={S.card}>
          <p style={S.cardTitle}>Import GEDCOM</p>
          <label style={S.fileBox}>
            {gedFile ? `✓ ${gedFile.name}` : "Click to select a .ged file"}
            <input type="file" accept=".ged" style={{ display: "none" }}
              onChange={e => { setGedFile(e.target.files?.[0] ?? null); setGedMsg(null); }} />
          </label>
          {gedFile && (
            <div style={{ marginTop: "0.75rem" }}>
              <button style={S.btn} onClick={uploadGedcom} disabled={uploading}>
                {uploading ? "Uploading…" : "Upload & Import"}
              </button>
            </div>
          )}
          {gedMsg && <p style={{ ...S.msg, ...(gedMsg.ok ? S.ok : S.err) }}>{gedMsg.text}</p>}
        </div>

        {/* WhatsApp mapping */}
        <div style={S.card}>
          <p style={S.cardTitle}>Map WhatsApp to Person</p>
          <div style={{ ...S.row, ...S.mb }}>
            <div style={{ flex: 1 }}>
              <label style={S.label}>Person ID</label>
              <input style={S.input} placeholder="e.g. I1" value={waId} onChange={e => setWaId(e.target.value)} />
            </div>
            <div style={{ flex: 2 }}>
              <label style={S.label}>WhatsApp number</label>
              <input style={S.input} placeholder="e.g. +48123456789" value={waPhone} onChange={e => setWaPhone(e.target.value)} />
            </div>
            <button style={S.btn} onClick={mapWhatsapp} disabled={!waId || !waPhone}>Map</button>
          </div>
          {waMsg && <p style={{ ...S.msg, ...(waMsg.ok ? S.ok : S.err) }}>{waMsg.text}</p>}
        </div>

        {/* Persons list */}
        <div style={S.card}>
          <div style={{ display: "flex", alignItems: "center", marginBottom: "1rem" }}>
            <p style={{ ...S.cardTitle, margin: 0, flex: 1 }}>Persons ({persons.length})</p>
            <button style={S.btnSm} onClick={loadPersons} disabled={loadingP}>
              {loadingP ? "Loading…" : "Refresh"}
            </button>
          </div>
          {persons.length === 0
            ? <p style={S.empty}>{saved ? "No persons yet. Import a GEDCOM file." : "Save your API key to load persons."}</p>
            : (
              <table style={S.table}>
                <thead>
                  <tr>
                    <th style={S.th}>ID</th>
                    <th style={S.th}>Name</th>
                    <th style={S.th}>WhatsApp</th>
                  </tr>
                </thead>
                <tbody>
                  {persons.map(p => (
                    <tr key={p.id}>
                      <td style={S.td}><span style={S.badge}>{p.id}</span></td>
                      <td style={S.td}>{p.name}</td>
                      <td style={S.td}>{p.whatsapp ?? <span style={{ color: "#aaa" }}>—</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )
          }
        </div>

      </div>
    </div>
  );
}
