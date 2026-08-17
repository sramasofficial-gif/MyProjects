import { useState } from "react";

export default function PromptBar() {

    const [prompt, setPrompt] = useState("");

    const sendPrompt = () => {

        console.log(prompt);

        setPrompt("");
    };

    return (

        <div className="prompt-bar">

            <input
                value={prompt}
                onChange={(e) =>
                    setPrompt(e.target.value)
                }
                placeholder="Ask Copilot..."
            />

            <button onClick={sendPrompt}>
                Send
            </button>

        </div>

    );
}