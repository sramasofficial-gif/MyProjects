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

// ==============================================================================
// 🟢 FIXED EXPORT TRIGGER: Bypasses HTML Canvas completely to prevent Tainted Canvas errors
// ==============================================================================
export function ExportPNGButton({ canvasSelectorId, filename = "diagram.png" }) {
    const exportToSvg = () => {
        // Target the parent workplane container holding your active graph elements
        const container = document.getElementById(canvasSelectorId);
        const svgElement = container?.querySelector('svg');
        
        if (!svgElement) {
            alert("No display canvas element found to extract vector definitions.");
            return;
        }

        try {
            // Clone the active DOM element node to prevent messing up the visible graph layout
            const clonedSvg = svgElement.cloneNode(true);
            
            // Explicitly extract layout coordinates to preserve clear bounds
            const viewBox = clonedSvg.getAttribute("viewBox");
            if (viewBox) {
                const [, , width, height] = viewBox.split(" ");
                clonedSvg.setAttribute("width", width);
                clonedSvg.setAttribute("height", height);
            } else {
                // Fallback layout bounding settings if viewBox attributes are absent
                const rect = svgElement.getBoundingClientRect();
                clonedSvg.setAttribute("width", rect.width || "100%");
                clonedSvg.setAttribute("height", rect.height || "600");
            }

            // Ensure XML serialization metadata elements are safely attached
            clonedSvg.setAttribute("xmlns", "http://w3.org");

            // Convert the vector DOM nodes directly into an encoded text string stream
            const svgSerializer = new XMLSerializer();
            let svgString = svgSerializer.serializeToString(clonedSvg);

            // Clean up any remaining HTML entity markers inside custom label tags
            svgString = svgString.replace(/&nbsp;/g, " ");

            // Create a clean data blob from the text stream
            const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
            const downloadUrl = window.URL.createObjectURL(svgBlob);

            // Force a native, client-side browser file download
            const linkElement = document.createElement('a');
            linkElement.href = downloadUrl;
            
            // Dynamically change file extension parameter configurations to safe .svg format
            const safeSvgFilename = filename.replace(/\.png$/i, '.svg');
            linkElement.download = safeSvgFilename;
            
            document.body.appendChild(linkElement);
            linkElement.click();
            
            // Clean up resources to prevent memory leaks
            document.body.removeChild(linkElement);
            window.URL.revokeObjectURL(downloadUrl);

        } catch (err) {
            console.error("Export module encountered a vector tracking error:", err);
            alert(`Failed to save image: ${err.message}`);
        }
    };

    return (
        <button 
            className="diagram-source-button" 
            onClick={exportToSvg} 
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
        >
            💾 Save SVG Image
        </button>
    );
}