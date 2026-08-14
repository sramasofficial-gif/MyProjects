import { useEffect, useState } from "react";
import { loadRepoTree } from "../services/api";

export default function RepoExplorer({
    selectedFile,
    onFileSelect
}) {

    const [repo, setRepo] = useState([]);
    const [expandedFolders, setExpandedFolders] = useState({});

    const toggleFolder = (folder) => {

        setExpandedFolders(prev => ({
            ...prev,
            [folder]: !prev[folder]
        }));
    };

    useEffect(() => {

        loadRepoTree()
            .then(setRepo);

    }, []);

    return (

        <div className="repo-panel" style={{background: "#f8f9fa"}}>

            <div className="repo-title">
                Repo Explorer
            </div>

            {repo.map(section => (

                <div key={section.folder}>

                    <div
                        className="folder"
                        onClick={() =>
                            toggleFolder(section.folder)
                        }
                        style={{
                            cursor: "pointer",
                            fontWeight: "bold"
                        }}
                    >

                        {expandedFolders[section.folder]
                            ? "▼ "
                            : "▶ "}

                        {section.folder}

                    </div>

                    {expandedFolders[section.folder] && 
                        section.files.map(file => (

                        <div
                            key={file}
                            className={
                                selectedFile ===
                                `${section.folder}/${file}`
                                    ? "file selected"
                                    : "file"
                            }
                            onClick={() => {
                                const selected =`${section.folder}/${file}`;
                                console.log(
                                    "Selected:",
                                    selected
                                    );
                                onFileSelect(selected);
                            }}
                        >
                            📄 {file}
                        </div>

                    ))}
                </div>

            ))}
        </div>
    );
}