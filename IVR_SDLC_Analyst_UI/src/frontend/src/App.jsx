// MyProjects/IVR_SDLC_Analyst_UI/src/frontend/src/App.jsx
import React, { useState } from 'react';
import MainLayout from './layout/MainLayout';
import HLDAnalyzer from './components/HLDAnalyzer';
// 🟢 IMPORT: Bring in your dedicated setup workspace file view
import { SystemSettingsPage } from './components/SystemSettingsPage';

export default function App() {
    // Elevate active tracking hooks to support settings routes maps seamlessly
    const [activeSection, setActiveSection] = useState('repository');
    const [selectedFile, setSelectedFile] = useState(null);

    return (
        <div className="app-layout">
            {/* Top Level Master Corporate Application Header Header */}
            <header className="header">
                <div style={{ display: 'flex', width: '100%', alignItems: 'center', paddingRight: '20px' }}>
                    
                    {/* Left Title Workspace Block with new Header corner option button linked inside */}
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                        <span style={{ fontSize: '20px', fontWeight: '700', letterSpacing: '-0.02em' }}>
                            🎙️ IVR SDLC Automated Analyst Platform
                        </span>
                        
                        {/* 🟢 ENHANCEMENT: Clickable Settings Icon corner button explicitly aligned on the right side of the title string */}
                        <button 
                            className={`settings-header-icon ${activeSection === 'settings' ? 'active' : ''}`}
                            title="Open Platform Administration System Config"
                            onClick={() => setActiveSection('settings')}
                        >
                            ⚙️
                        </button>
                    </div>
                    
                    {/* Shell Top-Level Functional Navigation Switch Panel Tabs */}
                    <nav style={{ marginLeft: 'auto', display: 'flex', gap: '12px' }}>
                        <button 
                            className={`tab ${activeSection === 'repository' ? 'active' : ''}`}
                            style={{ minWidth: '130px', padding: '6px 14px', fontSize: '13px', borderRadius: '4px' }}
                            onClick={() => setActiveSection('repository')}
                        >
                            📦 Dev Workspace
                        </button>
                        <button 
                            className={`tab ${activeSection === 'hld-analyzer' ? 'active' : ''}`}
                            style={{ minWidth: '130px', padding: '6px 14px', fontSize: '13px', borderRadius: '4px' }}
                            onClick={() => setActiveSection('hld-analyzer')}
                        >
                            📋 HLD Analyzer
                        </button>
                    </nav>
                </div>
            </header>

            {/* Old inline panel placeholder text clean space removed completely from here */}

            {/* Dynamic Core Screen Router Container Workspace Viewport */}
            <main style={{ flex: 1, display: 'flex', overflow: 'hidden', background: '#f8fafc' }}>
                {(() => {
                    switch (activeSection) {
                        case 'repository':
                            return (
                                <MainLayout 
                                    selectedFile={selectedFile} 
                                    setSelectedFile={setSelectedFile} 
                                />
                            );
                        case 'hld-analyzer':
                            return <HLDAnalyzer />;
                        case 'settings':
                            // 🟢 RENDER TARGET: Direct isolates form parameters out to a dedicated clean configuration dashboard view
                            return <SystemSettingsPage />;
                        default:
                            return (
                                <MainLayout 
                                    selectedFile={selectedFile} 
                                    setSelectedFile={setSelectedFile} 
                                />
                            );
                    }
                })()}
            </main>
        </div>
    );
}
