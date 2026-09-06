import React, { useState, useEffect } from 'react';

export function SystemSettingsPanel() {
    const [settings, setSettings] = useState({
        enable_diagram_caching: true,
        enable_simulation_mode: false,
        enable_persistence: true
    });
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        fetch('http://localhost:8000/api/settings')
            .then(res => res.json())
            .then(data => setSettings(data))
            .catch(err => console.error("Failed to fetch environment server options", err));
    }, []);

    const toggleSetting = (key) => {
        const updated = { ...settings, [key]: !settings[key] };
        setSettings(updated);
        setSaving(true);

        fetch('http://localhost:8000/api/settings', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updated)
        })
        .then(res => res.json())
        .finally(() => setSaving(false));
    };

    return (
        <div className="executive-summary-card" style={{ marginBottom: '20px' }}>
            <h3 style={{ margin: '0 0 12px 0', color: '#1d3557' }}>⚙️ Global SDLC Server Orchestration Settings</h3>
            <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '14px', fontWeight: '600' }}>
                    <input type="checkbox" checked={settings.enable_diagram_caching} onChange={() => toggleSetting('enable_diagram_caching')} />
                    Enable Diagram Caching
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '14px', fontWeight: '600' }}>
                    <input type="checkbox" checked={settings.enable_simulation_mode} onChange={() => toggleSetting('enable_simulation_mode')} />
                    Enable Mock Server Simulation
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '14px', fontWeight: '600' }}>
                    <input type="checkbox" checked={settings.enable_persistence} onChange={() => toggleSetting('enable_persistence')} />
                    Enable Disk Local Persistence
                </label>
                {saving && <span style={{ fontSize: '12px', color: '#0969da' }} className="refresh-icon spinning">⏳ Syncing...</span>}
            </div>
        </div>
    );
}

// 🟢 EXPORT FUNCTION: Renders a high-fidelity image download trigger button
export function ExportPNGButton({ canvasSelectorId, filename = "diagram.png" }) {
    const exportToPng = () => {
        // Target the parent container element containing the inner dynamic node SVG
        const container = document.getElementById(canvasSelectorId);
        const svgElement = container?.querySelector('svg');
        
        if (!svgElement) {
            alert("No display canvas element generated found to render snapshot extraction.");
            return;
        }

        try {
            const svgString = new XMLSerializer().serializeToString(svgElement);
            const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
            const URL = window.URL || window.webkitURL || window;
            const blobURL = URL.createObjectURL(svgBlob);
            
            const image = new Image();
            image.onload = () => {
                const canvas = document.createElement('canvas');
                // Capture bounding dimensions of the active SVG target element node canvas layout fields
                const bbox = svgElement.getBBox();
                canvas.width = bbox.width + 40;
                canvas.height = bbox.height + 40;
                
                const context = canvas.getContext('2d');
                if (context) {
                    context.fillStyle = '#ffffff';
                    context.fillRect(0, 0, canvas.width, canvas.height);
                    context.drawImage(image, 20, 20);
                    
                    const pngURL = canvas.toDataURL('image/png');
                    const downloadLink = document.createElement('a');
                    downloadLink.href = pngURL;
                    downloadLink.download = filename;
                    document.body.appendChild(downloadLink);
                    downloadLink.click();
                    document.body.removeChild(downloadLink);
                }
            };
            image.src = blobURL;
        } catch (err) {
            console.error("Export to graphic matrix file generated failure", err);
        }
    };

    return (
        <button className="diagram-source-button" onClick={exportToPng} style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
            💾 Save PNG Image
        </button>
    );
}