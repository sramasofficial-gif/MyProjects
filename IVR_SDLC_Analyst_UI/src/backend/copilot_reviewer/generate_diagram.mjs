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

            // Open generate_diagram.mjs and update the inner readline loop processing step block:
            try {
                const request = JSON.parse(line);
                const fileKey = `${request.relativePath}::${request.source.length}`;

                // 1. Initialize or reset chat session context structures if document signatures update
                if (!session || initializedFileKey !== fileKey) {
                    if (session?.destroy) await session.destroy().catch(() => {});
                    
                    let systemPrompt = "";
                    
                    // 🟢 INTERCEPT: Switch system configuration roles depending on the task parameters
                    if (request.diagramType === "HLD_SEGMENTATION_MODE") {
                        systemPrompt = `You are an expert Enterprise Systems Analyst. Your goal is to receive unstructured High-Level Design (HLD) text content data scraped from corporate wikis and categorize them down into valid structured JSON fragments following strict classification schemas.`;
                    } else {
                        systemPrompt = `You are an expert systems architect. You are analyzing the active code file: "${request.relativePath}". Source: ${request.source}. Convert parameters cleanly into strict Mermaid layout schema graphs.`;
                    }

                    session = await client.createSession({
                        systemMessage: { content: systemPrompt.trim() }
                    });
                    initializedFileKey = fileKey;
                    
                    // Push raw text content file assets down conversation pipeline stream once
                    await session.sendAndWait({ 
                        prompt: `Here is the raw text context payload body for tracking: "${request.relativePath}":\n\n${request.source}\n\nAcknowledge parsing readiness with 'READY'.` 
                    });
                }

                // 2. Define operational execution prompts targeting task definitions
                let specificPrompt = "";
                
                if (request.diagramType === "HLD_SEGMENTATION_MODE") {
                    // 🟢 Strict structured blueprint prompt instruction set
                    specificPrompt = `
            Analyze the initialized wiki text content and isolate structural functional criteria parameter sets. Split data points down matching this strict JSON layout contract specification exactly.

            Required JSON Structure:
            {
            "document_metadata": { "title": "${request.relativePath}", "segments_found": 2 },
            "review_required_sections": [
                {
                "section_title": "Isolate section header or name context",
                "context_summary": "Brief summary explaining why this section demands code reviews",
                "raw_text_content": "Literal extracted text criteria block matching this component"
                }
            ],
            "ivr_flow_requirements": [
                {
                "flow_name": "Isolate the name or ID profile of this IVR routing path channel",
                "trigger_condition": "Events causing this flow branch to activate (e.g. Menu choice 2, Card block)",
                "intended_steps": [
                    "Step 1 operation description text",
                    "Step 2 operation description text"
                ]
                }
            ]
            }

            CRITICAL RULES:
            - Output valid, minified JSON text data ONLY.
            - Do NOT wrap code blocks inside markdown ticks (\`\`\`).
            - Ensure all inner quotation tags, commas, and arrays validate completely against standard JSON parsers.
            - Do NOT output intro/outro conversational remarks.
            `.trim();
                } else {
                    // Normal diagram compilation instructions
                    specificPrompt = `Generate a high-quality, professional-grade ${request.diagramType} layout string mapping the initialized file code parameters cleanly using strict Mermaid syntax guidelines. Check node tags and bracket strings to prevent compilation errors. Output raw syntax ONLY.`;
                }

                // 3. Dispatch prompt to the current live active chat session thread
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
