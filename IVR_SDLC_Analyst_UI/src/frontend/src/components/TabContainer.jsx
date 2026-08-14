import { useEffect, useState } from "react";
import { loadFile } from "../services/api";

export default function TabContainer({
    selectedFile
}) {

    const [content, setContent] =
        useState("");

    useEffect(() => {

        if (!selectedFile)
            return;

        console.log(
            "selectedFile:",
            selectedFile
            );

        loadFile(selectedFile)
            .then(data =>
                setContent(data.content)
            );

    }, [selectedFile]);

    return (

        <div className="main-panel">

            <div
            style={{
                padding: "10px",
                borderBottom:
                "1px solid lightgray"
            }}
            >

            <button>
                Dashboard
            </button>

            <button>
                Flow
            </button>

            <button>
                Lambda
            </button>

            <button>
                Terraform
            </button>

            <button>
                Chat
            </button>

            </div>

            <div className="tab-content">

                <pre>
                    {content}
                </pre>

            </div>

        </div>

    );
}

