import process from "node:process";
import { CopilotClient, RuntimeConnection } from "@github/copilot-sdk";

async function readStandardInput() {
    let input = "";
    for await (const chunk of process.stdin) { input += chunk; }
    if (!input.trim()) throw new Error("No payload was supplied via stdin.");
    return JSON.parse(input);
}

/*
function createDiagramPrompt(relativePath, source, diagramType) {
    return `
Analyze the following AWS Lambda source file and generate a high-quality ${diagramType} layout string using Mermaid syntax.

File Path Reference: ${relativePath}
Source Code Manifest:
${source}

Strict Formatting Blueprint Guidelines:
1. If diagramType is "sequence", output a sequence diagram using "sequenceDiagram". Add "autonumber" at the top. Use vertical activation flags ("+" and "-") to clearly mark lifelines. Use explicit method parameter lists on call arrows, and track variable mappings on response paths. Extract structural internal business blocks using native "loop ... end" and "alt ... else ... end" frames.
2. If diagramType is "flowchart", output a flowchart mapping complex logic switches using "flowchart TD".
3. If diagramType is "dependency", output an architectural import tree layout using "graph LR".
4. Return the raw Mermaid layout data ONLY. Do NOT use Markdown code blocks or wrapping tick backfences (\`\`\`). Do NOT include any intro or conversational text before or after the code snippet.
`.trim();
}
*/

/*
function createDiagramPrompt(relativePath, source, diagramType) {
    return `
Analyze the following AWS Lambda source file and generate a high-quality, professional-grade ${diagramType} layout string using strict Mermaid syntax.

File Path Reference: ${relativePath}
Source Code Manifest:
${source}

Strict Formatting Blueprint Guidelines:

1. If diagramType is "sequence":
   - Start with "sequenceDiagram" and add "autonumber" at the top.
   - Use vertical activation flags ("+" and "-") to clearly mark execution lifelines.
   - Include explicit method parameter lists on call arrows and track variable mappings on response paths.
   - Extract structural internal business blocks using native "loop ... end" and "alt ... else ... end" frames.

2. If diagramType is "flowchart":
   - Start with "flowchart TD" to represent the detailed operational step-by-step logic path.
   - Represent conditional evaluations (if/else, switch blocks) using diamond nodes: \`nodeId{Condition text}\`.
   - Represent operational statements, database interactions, or external fetches using rectangular nodes: \`nodeId[Process step description]\`.
   - Ensure the flowchart traces cleanly from an initial "Start" node down to terminal "End" or "Return" nodes.

3. If diagramType is "dependency":
   - Start with "graph LR" to showcase an architectural import tree.
   - Place the primary Lambda file at the center root node.
   - Parse all standard imports, corporate service clients, repositories, and third-party NPM modules used in the file.
   - Map connections from the Lambda root out to these dependencies using clean structural mapping arrows: \`Lambda --> ModuleID["module-name"]\`.

General Rules:
- Return the raw Mermaid layout data ONLY.
- Do NOT wrap the output in Markdown code blocks or backfences (\`\`\`).
- Do NOT include any introductory, conversational, or concluding text before or after the diagram text.
- Ensure all brackets, parentheses, and text string values within nodes are closed perfectly.
`.trim();
}
*/

function createDiagramPrompt(relativePath, source, diagramType) {
    return `
Analyze the following AWS Lambda source file and generate a high-quality, professional-grade ${diagramType} layout string using strict Mermaid syntax.

File Path Reference: ${relativePath}
Source Code Manifest:
${source}

Strict Formatting Blueprint Guidelines:
1. If diagramType is "sequence":
   - Start with "sequenceDiagram" and add "autonumber" at the top.
   - Use vertical activation flags ("+" and "-") to mark lifelines.

2. If diagramType is "flowchart":
   - Start with "flowchart TD".

3. If diagramType is "dependency":
   - Start with "graph LR".
   - CRITICAL RULE FOR ALL DIAGRAM TYPES: Node identifiers MUST be alphanumeric values only without special symbols (e.g., use "RootLambda" or "CommonModule"). 
   - NEVER use paths, slashes (/ or \\), dots (.), or at symbols (@) directly as unquoted node IDs. 
   - Always map nodes cleanly with clear textual labels in quotes, exactly like this template format example: RootLambda["GetPrimaryCardDetails/index.ts"] --> CommonModule["@ccrlayer/common"]

General Rules:
- Return the raw Mermaid layout data ONLY. Do NOT use Markdown code blocks or wrapping tick backfences (\`\`\`).
- Do NOT include conversational text.
`.trim();
}



async function main() {
    let client = null;
    let session = null;
    try {
        const request = await readStandardInput();
        const secureToken = process.env.COPILOT_GITHUB_TOKEN ?? process.env.GITHUB_TOKEN;

        client = new CopilotClient({
            connection: RuntimeConnection.forStdio(),
            useLoggedInUser: true
        });
        
        await client.start();
        
        session = await client.createSession({
            systemMessage: {
                content: `You are an expert systems architect. Translate source code into clean, detailed, syntactically perfect Mermaid diagram strings matching the type parameter requested exactly.`
            }
        });

        const prompt = createDiagramPrompt(request.relativePath, request.source, request.diagramType);
        // 🟢 Update the response resolution logic inside your generate_diagram.mjs file

        const response = await session.sendAndWait({ prompt });

        // The official GitHub Copilot SDK maps completions strictly under response.data.content
        let rawText = "";

        if (typeof response === "string") {
            rawText = response;
        } else if (response?.data?.content) {
            rawText = response.data.content; // 🟢 Official SDK property destination pointer
        } else if (response?.content) {
            rawText = response.content;
        } else if (response?.message?.content) {
            rawText = response.message.content;
        }

        rawText = (rawText || "").trim();

        // Add a clear structural log in case the model drops an empty token block 
        if (!rawText) {
            console.error("[SDK DIAGNOSTIC] Unexpected response tree structure received:", JSON.stringify(response));
        }

        // Clean up markdown block leak tags before stringification
        rawText = rawText
            .replace(/^```[a-z]*\s*/i, "")
            .replace(/\s*```$/i, "")
            .trim();

        process.stdout.write(JSON.stringify({ success: true, mermaid_string: rawText }) + "\n");

    } catch (error) {
        process.stdout.write(JSON.stringify({ success: false, error: String(error) }) + "\n");
        process.exitCode = 1;
    } finally {
        if (session?.destroy) try { await session.destroy(); } catch {}
        if (client?.stop) try { await client.stop(); } catch {}
    }
}

await main();
