import { useNavigate } from "react-router-dom";
import ChatInterface from "../components/ChatInterface";

const styles: Record<string, React.CSSProperties> = {
  page: {
    display: "flex",
    flexDirection: "column" as const,
    height: "100vh",
    background: "#f5f5f5",
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0.75rem 1.5rem",
    background: "#2563eb",
    color: "#fff",
  },
  title: { margin: 0, fontSize: "1.1rem", fontWeight: 700 },
  logoutBtn: {
    background: "rgba(255,255,255,0.2)",
    border: "none",
    color: "#fff",
    padding: "0.35rem 0.8rem",
    borderRadius: 8,
    cursor: "pointer",
    fontSize: "0.85rem",
  },
  chatBox: {
    flex: 1,
    display: "flex",
    flexDirection: "column" as const,
    maxWidth: 720,
    width: "100%",
    margin: "0 auto",
    background: "#f5f5f5",
    overflow: "hidden",
  },
};

export default function Chat() {
  const navigate = useNavigate();
  const userId = localStorage.getItem("userId") ?? "";

  function handleLogout() {
    localStorage.removeItem("userId");
    navigate("/login");
  }

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <h1 style={styles.title}>Family Tree Assistant</h1>
        <button style={styles.logoutBtn} onClick={handleLogout}>
          Logout
        </button>
      </header>
      <div style={styles.chatBox}>
        <ChatInterface userId={userId} />
      </div>
    </div>
  );
}
