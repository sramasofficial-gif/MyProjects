import { useState } from "react";
import RepoExplorer from "../components/RepoExplorer";
import TabContainer from "../components/TabContainer";
import PromptBar from "../components/PromptBar";

export default function MainLayout() {

    const [selectedFile, setSelectedFile] = useState(null);

    return (
        <div className="app-layout">

            <header className="header">
                Amazon Connect SDLC Agent
            </header>

            <div className="content">

                <RepoExplorer
                    onFileSelect={setSelectedFile}
                />

                <TabContainer
                    selectedFile={selectedFile}
                />

            </div>

            <PromptBar />

        </div>
    );
}