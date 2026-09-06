import { useState } from "react";
// 🟢 1. IMPORT YOUR REAL CORE LAYOUT CONTAINER FILE:
import MainLayout from "./layout/MainLayout"; 
// 🟢 2. IMPORT YOUR NEW WIKI ANALYZER COMPONENT VIEW:
import HLDAnalyzer from "./components/HLDAnalyzer";

export default function App() {
    // Manage active top-level structural tab workspaces
    const [activeSection, setActiveSection] = useState("repository");

    return (
        <main className="app-shell-layout" style={{ minHeight: "100vh", display: "flex", flexDirection: "column", background: "#f8fafc" }}>
            
            {/* Enterprise Top Header Control Navigation Row Banner */}
            <header style={{ background: "#ffffff", borderBottom: "1px solid #e2e8f0", padding: "12px 24px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <div style={{ background: "#0f6cbd", width: "12px", height: "12px", borderRadius: "50%" }} />
                    <h1 style={{ margin: 0, fontSize: "1.2rem", fontWeight: "700", color: "#1e293b" }}>IVR SDLC Analyst Platform</h1>
                </div>

                {/* Primary Multi-Pane Tab Selection Navigation Dashboard */}
                <nav style={{ display: "flex", gap: "8px", background: "#f1f5f9", padding: "4px", borderRadius: "6px" }}>
                    <button 
                        onClick={() => setActiveSection("repository")}
                        style={{
                            padding: "6px 16px",
                            border: "none",
                            borderRadius: "4px",
                            fontSize: "0.9rem",
                            fontWeight: "600",
                            cursor: "pointer",
                            background: activeSection === "repository" ? "#ffffff" : "transparent",
                            color: activeSection === "repository" ? "#0f6cbd" : "#475569",
                            boxShadow: activeSection === "repository" ? "0 1px 3px rgba(0,0,0,0.1)" : "none",
                            transition: "all 0.15s ease"
                        }}
                    >
                        📁 Repository Code Workspace
                    </button>
                    <button 
                        onClick={() => setActiveSection("hld-analyzer")}
                        style={{
                            padding: "6px 16px",
                            border: "none",
                            borderRadius: "4px",
                            fontSize: "0.9rem",
                            fontWeight: "600",
                            cursor: "pointer",
                            background: activeSection === "hld-analyzer" ? "#ffffff" : "transparent",
                            color: activeSection === "hld-analyzer" ? "#0f6cbd" : "#475569",
                            boxShadow: activeSection === "hld-analyzer" ? "0 1px 3px rgba(0,0,0,0.1)" : "none",
                            transition: "all 0.15s ease"
                        }}
                    >
                        📋 Wiki HLD Analyzer
                    </button>
                </nav>
                
                <div style={{ fontSize: "0.85rem", color: "#64748b" }}>GitHub Copilot SDK Active</div>
            </header>

            {/* Dynamic Viewport Dashboard Switching Pane Area */}
            <div className="workspace-viewport-pane" style={{ flex: 1, display: "flex", flexDirection: "column" }}>
                {activeSection === "repository" ? (
                    // 🟢 Serves your original layout configuration tree view and prompt panel exactly as it was
                    <MainLayout /> 
                ) : (
                    // 🟢 Serves the newly added wiki analysis blueprint engine console panel
                    <HLDAnalyzer />
                )}
            </div>

        </main>
    );
}
