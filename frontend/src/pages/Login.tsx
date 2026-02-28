import { useState } from "react";
import { useNavigate } from "react-router-dom";

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "100vh",
    background: "#f5f5f5",
  },
  card: {
    background: "#fff",
    borderRadius: 12,
    padding: "2.5rem 2rem",
    boxShadow: "0 2px 16px rgba(0,0,0,0.1)",
    width: 340,
    textAlign: "center" as const,
  },
  title: { margin: "0 0 0.25rem", fontSize: "1.5rem", fontWeight: 700 },
  subtitle: { margin: "0 0 2rem", color: "#666", fontSize: "0.9rem" },
  label: { display: "block", textAlign: "left" as const, marginBottom: "0.4rem", fontSize: "0.85rem", fontWeight: 600 },
  input: {
    width: "100%",
    padding: "0.6rem 0.8rem",
    border: "1px solid #ddd",
    borderRadius: 6,
    fontSize: "1rem",
    marginBottom: "1rem",
  },
  button: {
    width: "100%",
    padding: "0.75rem",
    background: "#2563eb",
    color: "#fff",
    border: "none",
    borderRadius: 6,
    fontSize: "1rem",
    fontWeight: 600,
    cursor: "pointer",
  },
  error: { color: "#dc2626", fontSize: "0.85rem", marginTop: "0.5rem" },
};

export default function Login() {
  const [userId, setUserId] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const id = userId.trim();
    if (!id) {
      setError("Please enter your Person ID.");
      return;
    }
    localStorage.setItem("userId", id);
    navigate("/");
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>Family Tree</h1>
        <p style={styles.subtitle}>AI-powered family assistant</p>
        <form onSubmit={handleSubmit}>
          <label style={styles.label} htmlFor="userId">
            Your Person ID
          </label>
          <input
            id="userId"
            style={styles.input}
            type="text"
            placeholder="e.g. I1"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            autoFocus
          />
          {error && <p style={styles.error}>{error}</p>}
          <button style={styles.button} type="submit">
            Enter
          </button>
        </form>
      </div>
    </div>
  );
}
