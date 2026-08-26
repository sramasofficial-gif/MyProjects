import process from "node:process";
import readline from "node:readline";
import { CopilotClient, RuntimeConnection } from "@github/copilot-sdk";

async function main() {
    let client = null;
    let session = null;
    let initializedFileKey = null;

    try {
        // 1. Establish the core SDK framework engine once at process launch
        client = new CopilotClient({
            connection: RuntimeConnection.forStdio(),
            useLoggedInUser: true
        });
        await client.start();

        // 2. Open up a continuous line-by-line reading interface stream
        const rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout,
            terminal: false
        });

        for await (const line of rl) {
            if (!line.trim()) continue;

            try {
                const request = JSON.parse(line);
                const fileKey = `${request.relativePath}::${request.source.length}`;

                // 3. Structural optimization: Initialize/Reuse session conditionally
                if (!session || initializedFileKey !== fileKey) {
                    if (session?.destroy) await session.destroy().catch(() => {});
                    
                    // Inject file code assets strictly once inside the foundational system instruction message
                    session = await client.createSession({
                        systemMessage: {
                            content: `
You are an expert systems architect. You are analyzing the active code file: "${request.relativePath}".
Source Code File Text:
${request.source}

When requested, convert this specific source code framework context cleanly into syntactically sound Mermaid diagrams.
Return the raw Mermaid code block data ONLY. Do NOT use Markdown formatting blocks or code tick backfences (\`\`\`). Do NOT inject introductory or conversational sentences.
`.trim()
                        }
                    });
                    initializedFileKey = fileKey;
                }

                // 4. Send light prompt adjustments on subsequent canvas tab selections
                const specificPrompt = `Generate a high-quality, professional-grade ${request.diagramType} layout string mapping the initialized file code parameters cleanly using strict Mermaid syntax guidelines. Check node tags and bracket strings to prevent compilation errors.`;
                
                const response = await session.sendAndWait({ prompt: specificPrompt });
                
                let rawText = "";
                if (typeof response === "string") { rawText = response; }
                else if (response?.data?.content) { rawText = response.data.content; }
                else if (response?.content) { rawText = response.content; }
                else if (response?.message?.content) { rawText = response.message.content; }

                rawText = (rawText || "").trim()
                    .replace(/^```[a-z]*\s*/i, "")
                    .replace(/\s*```$/i, "")
                    .trim();

                // Direct output back safely using a singular serialized string line block
                process.stdout.write(JSON.stringify({ success: true, mermaid_string: rawText }) + "\n");

            } catch (innerError) {
                process.stdout.write(JSON.stringify({ success: false, error: String(innerError) }) + "\n");
            }
        }
    } catch (globalError) {
        process.stderr.write(`Daemon Crash Exception: ${String(globalError)}\n`);
        process.exit(1);
    }
}

await main();
