// MyProjects/IVR_SDLC_Analyst_UI/src/frontend/src/components/SystemSettingsPage.jsx
import React, { useState, useEffect } from 'react';

export function SystemSettingsPage() {
    const [settings, setSettings] = useState({
        enable_diagram_caching: true,
        enable_simulation_mode: false,
        enable_persistence: true
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [statusMessage, setStatusMessage] = useState({ text: "", isError: false });

    // Fetch live configuration limits on component mount
    useEffect(() => {
        fetch('http://localhost:8000/api/settings')
            .then(res => {
                if (!res.ok) throw new Error("Server options tracking offline.");
                return res.json();
            })
            .then(data => {
                setSettings(data);
                setLoading(false);
            })
            .catch(err => {
                console.error(err);
                setStatusMessage({ text: "Failed to pull down live backend options state flags.", isError: true });
                setLoading(false);
            });
    }, []);

    const handleChange = (key) => {
        setSettings(prev => ({ ...prev, [key]: !prev[key] }));
    };

    // Explicit submission router that pushes profiles down to server config matrices
    const handleSave = (e) => {
        e.preventDefault();
        setSaving(true);
        setStatusMessage({ text: "", isError: false });

        fetch('http://localhost:8000/api/settings', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        })
        .then(res => {
            if (!res.ok) throw new Error("Failed to write structural context properties.");
            return res.json();
        })
        .then(() => {
            setStatusMessage({ text: "⚙️ Global server settings successfully synchronized!", isError: false });
            // Automatic cleanup timer for standard user confirmation status rows
            setTimeout(() => setStatusMessage({ text: "", isError: false }), 4000);
        })
        .catch(err => {
            setStatusMessage({ text: `Failed to commit updates: ${err.message}`, isError: true });
        })
        .finally(() => setSaving(false));
    };

    if (loading) {
        return (
            <div className="loading-message">
                <div className="loading-spinner"></div>
                <span>Retrieving environment state configurations from the gateway...</span>
            </div>
        );
    }

    return (
        <div className="settings-container">
            <div style={{ borderBottom: '2px solid #e2e8f0', paddingBottom: '12px', marginBottom: '20px' }}>
                <h2 style={{ margin: 0, color: '#1d3557', fontSize: '22px' }}>🛠️ Global System Orchestration Control Plane</h2>
                <p style={{ margin: '4px 0 0 0', color: '#64748b', fontSize: '13px' }}>Modify application execution states, compiler loops, and token caching metrics variables dynamically.</p>
            </div>

            {statusMessage.text && (
                <div className={statusMessage.isError ? "error-message" : "loading-message"} style={{ background: statusMessage.isError ? '#fff0f0' : '#eef6ff' }}>
                    <span>{statusMessage.text}</span>
                </div>
            )}

            <form onSubmit={handleSave}>
                <div className="settings-row">
                    <div className="settings-info">
                        <h4>Enable Diagram Caching</h4>
                        <p>Saves parsed prompt parameters to prevent redundant calls to the Copilot Engine.</p>
                    </div>
                    <input 
                        type="checkbox" 
                        style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                        checked={settings.enable_diagram_caching} 
                        onChange={() => handleChange('enable_diagram_caching')} 
                    />
                </div>

                <div className="settings-row">
                    <div className="settings-info">
                        <h4>Enable Mock Server Simulation Mode</h4>
                        <p>Intercepts chart generation pipelines to dispatch immediate dummy string outputs.</p>
                    </div>
                    <input 
                        type="checkbox" 
                        style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                        checked={settings.enable_simulation_mode} 
                        onChange={() => handleChange('enable_simulation_mode')} 
                    />
                </div>

                <div className="settings-row">
                    <div className="settings-info">
                        <h4>Enable Local Storage Disk Persistence</h4>
                        <p>Forces structural HLD validation chunk maps to serialize into static disk arrays.</p>
                    </div>
                    <input 
                        type="checkbox" 
                        style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                        checked={settings.enable_persistence} 
                        onChange={() => handleChange('enable_persistence')} 
                    />
                </div>

                <div style={{ marginTop: '28px', display: 'flex', justifyContent: 'flex-end' }}>
                    <button 
                        type="submit" 
                        className="refresh-button" 
                        disabled={saving}
                        style={{ minWidth: '180px' }}
                    >
                        {saving ? "🔄 Synchronizing..." : "💾 Save Configuration"}
                    </button>
                </div>
            </form>
        </div>
    );
}
