// MyProjects/IVR_SDLC_Analyst_UI/src/frontend/src/App.jsx
import React, { useState } from 'react';
import MainLayout from './layout/MainLayout';
import HLDAnalyzer from './components/HLDAnalyzer';
import { SystemSettingsPage } from './components/SystemSettingsPage';

export default function App() {
    const [activeSection, setActiveSection] = useState('repository');
    const [selectedFile, setSelectedFile] = useState(null);

    // 🟢 SAFE DESKTOP ROUTER: Moves logic outside of JSX return block to prevent page blanking
    const renderActiveSection = () => {
        try {
            switch (activeSection) {
                case 'repository':
                    return (
                        <MainLayout 
                            selectedFile={selectedFile} 
                            setSelectedFile={setSelectedFile} 
                        />
                    );
                case 'hld-analyzer':
                    // Make sure HLDAnalyzer handles internal states gracefully
                    return <HLDAnalyzer /> || <div style={{ padding: '20px' }}>HLD Analyzer View offline.</div>;
                case 'settings':
                    return <SystemSettingsPage />;
                default:
                    return (
                        <MainLayout 
                            selectedFile={selectedFile} 
                            setSelectedFile={setSelectedFile} 
                        />
                    );
            }
        } catch (renderError) {
            console.error("Critical routing UI crash inside section:", activeSection, renderError);
            return (
                <div style={{ padding: '40px', color: '#991b1b', background: '#fef2f2', margin: '20px', borderRadius: '8px', border: '1px solid #fecaca' }}>
                    <h3>⚠️ Component Execution Error</h3>
                    <p>Failed to render active section panel view layer context properties safely.</p>
                    <button className="refresh-review-button" onClick={() => setActiveSection('repository')}>
                        Return to Dev Workspace
                    </button>
                </div>
            );
        }
    };

    return (
        <div className="app-layout">
            {/* Top Level Master Corporate Application Header Bar */}
            <header className="header">
                <div style={{ display: 'flex', width: '100%', alignItems: 'center' }}>
                    
                    {/* Left Title Workspace Block with gear icon corner button */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '18px', fontWeight: '700', letterSpacing: '-0.02em', color: '#ffffff' }}>
                            🎙️ IVR SDLC Automated Analyst Platform
                        </span>
                        
                        <button 
                            className={`settings-header-icon ${activeSection === 'settings' ? 'active' : ''}`}
                            title="Open Platform Administration System Config"
                            style={{ 
                                fontSize: '16px', 
                                padding: '6px',
                                background: activeSection === 'settings' ? 'rgba(255,255,255,0.2)' : 'transparent',
                                border: 'none',
                                cursor: 'pointer',
                                borderRadius: '50%'
                            }}
                            onClick={() => setActiveSection('settings')}
                        >
                            ⚙️
                        </button>
                    </div>
                    
                    {/* Top-Level Navigation Tabs */}
                    <nav style={{ marginLeft: 'auto', display: 'flex', gap: '8px' }}>
                        <button 
                            className="diagram-tab"
                            style={{ 
                                background: activeSection === 'repository' ? '#0f6cbd' : 'rgba(255,255,255,0.1)', 
                                color: '#ffffff',
                                border: 'none',
                                padding: '8px 16px',
                                borderRadius: '6px',
                                fontWeight: '600',
                                cursor: 'pointer'
                            }}
                            onClick={() => setActiveSection('repository')}
                        >
                            📦 Dev Workspace
                        </button>
                        <button 
                            className="diagram-tab"
                            style={{ 
                                background: activeSection === 'hld-analyzer' ? '#0f6cbd' : 'rgba(255,255,255,0.1)', 
                                color: '#ffffff',
                                border: 'none',
                                padding: '8px 16px',
                                borderRadius: '6px',
                                fontWeight: '600',
                                cursor: 'pointer'
                            }}
                            onClick={() => setActiveSection('hld-analyzer')}
                        >
                            📋 HLD Analyzer
                        </button>
                    </nav>
                </div>
            </header>

            {/* Main view container where sections dynamically render */}
            <main style={{ flex: 1, display: 'flex', overflow: 'hidden', background: '#f8fafc' }}>
                {renderActiveSection()}
            </main>
        </div>
    );
}
