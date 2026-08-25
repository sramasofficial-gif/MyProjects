function sanitizeMermaidName(name) {
    return String(name || "")
        .replace(/[^a-zA-Z0-9_]/g, "_");
}

function getLambdaName(filePath) {
    if (!filePath) {
        return "Lambda";
    }
    const parts = filePath.split(/[\\/]/);
    return parts[parts.length - 2] || "Lambda";
}

export function lambdaToSequence(content, selectedFile) {
    const lambdaName = getLambdaName(selectedFile);
    const calls = [];

    /*
     * Enhanced Regex:
     * Group 1: Optional variable assignment (e.g., const customerList = )
     * Group 2: Full object/method path (e.g., repository.lookup)
     * Group 3: Method parameters inside parentheses (e.g., primUserUrl, headers)
     */
    const advancedRegex = /(?:(?:const|let|var)\s+([a-zA-Z0-9_,\s{}]+)\s*=\s*)?await\s+([a-zA-Z0-9_.]+)\s*\(([^)]*)\)/g;
    
    let match;
    while ((match = advancedRegex.exec(content)) !== null) {
        const assignedVar = match[1] ? match[1].trim() : null;
        const fullInvocation = match[2].trim();
        const params = match[3] ? match[3].trim() : "";
        
        const participant = fullInvocation.split(".").pop();

        calls.push({
            participant,
            invocation: fullInvocation,
            parameters: params,
            responseVariable: assignedVar || "Response"
        });
    }

    const uniqueParticipants = [
        ...new Set(calls.map(c => c.participant))
    ];

    const lines = [];
    lines.push("sequenceDiagram");
    lines.push("    autonumber");
    lines.push("");

    // Setup Actors
    lines.push("    participant ContactFlow");
    lines.push(`    participant Lambda as ${lambdaName}`);
    lines.push("");

    uniqueParticipants.forEach(participant => {
        lines.push(`    participant ${sanitizeMermaidName(participant)}`);
    });

    lines.push("");
    lines.push("    ContactFlow->>+Lambda: Invoke (event)");
    lines.push("");

    // Process every captured call with its rich metadata
    calls.forEach((call, index) => {
        const target = sanitizeMermaidName(call.participant);
        
        // Formulate clean, scannable parameter strings for the arrow label
        const paramLabel = call.parameters ? `(${call.parameters})` : "()";
        
        // 1. Dispatch Request with full Input Details
        lines.push(`    Lambda->>+${target}: ${call.invocation}${paramLabel}`);
        
        // 2. Insert contextual visual notes for business logic blocks if loops/lookups are present
        if (call.parameters.toLowerCase().includes("url") || call.parameters.toLowerCase().includes("id")) {
            lines.push(`    Note over ${target}: Internal Logic:<br/>Process routing data parameters`);
        }

        // 3. Dispatch Response with exact Variable Names back to the lifecycle flow
        lines.push(`    ${target}-->>-Lambda: ${call.responseVariable}`);
        lines.push("");
    });

    lines.push("    Lambda-->>-ContactFlow: Final Response (statusCode)");

    return lines.join("\n");
}
