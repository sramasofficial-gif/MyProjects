import { useEffect, useState } from "react";
import { loadRepoTree } from "../services/api";

export default function RepoExplorer({
    selectedFile,
    onFileSelect
}) {
    const [repo, setRepo] = useState([]);
    const [expandedFolders, setExpandedFolders] = useState({});

    // Helper utility to resolve file icon variations based on extensions
    const getFileIcon = (filename) => {
        const ext = filename.split('.').pop().toLowerCase();
        switch (ext) {
            case 'json': return '📦';
            case 'js':
            case 'mjs':
            case 'ts':   return '⚙️';
            case 'tf':   return '☁️';
            default:     return '📄';
        }
    };

    // Helper utility to format folder display titles cleanly
    const formatFolderLabel = (folderName) => {
        if (folderName === "." || folderName === "") return "Root Repository";
        return folderName.replaceAll("\\", "/");
    };

    const toggleFolder = (folder) => {
        setExpandedFolders(prev => ({
            ...prev,
            [folder]: !prev[folder]
        }));
    };

    useEffect(() => {
        loadRepoTree()
            .then(data => {
                if (Array.isArray(data)) {
                    setRepo(data);
                    
                    // Auto-expand root directory folders on initial mount
                    const initialExpansion = {};
                    data.forEach(item => {
                        if (item.folder === "." || item.folder === "") {
                            initialExpansion[item.folder] = true;
                        }
                    });
                    setExpandedFolders(initialExpansion);
                }
            })
            .catch(err => console.error("Failed loading tree data matrix:", err));
    }, []);

    return (
        <div className="repo-panel" style={{ background: "#f8f9fa", padding: "12px", height: "100%", overflowY: "auto" }}>
            <div className="repo-title" style={{ fontWeight: "bold", fontSize: "14px", marginBottom: "12px", textTransform: "uppercase", color: "#495057", borderBottom: "1px solid #dee2e6", paddingBottom: "6px" }}>
                Repo Explorer
            </div>

            {repo.map(section => (
                <div key={section.folder} style={{ marginBottom: "6px" }}>
                    {/* Folder Row Header Component */}
                    <div
                        className="folder"
                        onClick={() => toggleFolder(section.folder)}
                        style={{
                            cursor: "pointer",
                            fontWeight: "600",
                            fontSize: "13px",
                            display: "flex",
                            alignItems: "center",
                            gap: "6px",
                            padding: "4px 6px",
                            borderRadius: "4px",
                            color: "#343a40",
                            userSelect: "none"
                        }}
                    >
                        <span style={{ fontSize: "10px", width: "12px" }}>
                            {expandedFolders[section.folder] ? "▼" : "▶"}
                        </span>
                        <span>📁 {formatFolderLabel(section.folder)}</span>
                    </div>

                    {/* Nested File Leaves Element Context */}
                    {expandedFolders[section.folder] && Array.isArray(section.files) && (
                        <div style={{ marginLeft: "4px" }}>
                            {section.files.map(file => {
                                // Cleanly combine paths by handling the root dot folder edge case
                                const targetPath = (section.folder === "." || section.folder === "") 
                                    ? file 
                                    : `${section.folder}/${file}`.replaceAll("\\", "/");

                                const isSelected = selectedFile === targetPath;

                                return (
                                    <div
                                        key={file}
                                        className={isSelected ? "file selected" : "file"}
                                        onClick={() => {
                                            console.log("Unified Selected Path URI:", targetPath);
                                            onFileSelect(targetPath);
                                        }}
                                        style={{
                                            padding: "4px 8px",
                                            cursor: "pointer",
                                            borderRadius: "4px",
                                            marginLeft: "16px",
                                            fontSize: "13px",
                                            display: "flex",
                                            alignItems: "center",
                                            gap: "6px",
                                            marginTop: "2px"
                                        }}
                                    >
                                        <span>{getFileIcon(file)}</span>
                                        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                            {file}
                                        </span>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            ))}
        </div>
    );
}
