// MyProjects/IVR_SDLC_Analyst_UI/src/frontend/src/components/MainLayout.jsx
import React from 'react';
import RepoExplorer from '../components/RepoExplorer';
import TabContainer from '../components/TabContainer';

export default function MainLayout({ selectedFile, setSelectedFile }) {
    return (
        <div className="content" style={{ width: '100%' }}>
            {/* Left Repository Sidebar Tree Explorer */}
            <div className="repo-panel">
                <div style={{ 
                    fontSize: '11px', 
                    fontWeight: '700', 
                    color: '#64748b', 
                    textTransform: 'uppercase', 
                    letterSpacing: '0.05em', 
                    marginBottom: '12px' 
                }}>
                    Repo Explorer
                </div>
                <RepoExplorer onFileSelect={setSelectedFile} selectedFile={selectedFile} />
            </div>

            {/* Right Main Focus Workspace Dashboard Control Plane */}
            <div className="main-panel">
                {/* 🟢 REMOVED: Mismatched sub-banner has been completely taken out to restore alignment */}
                <TabContainer selectedFile={selectedFile} />
            </div>
        </div>
    );
}
