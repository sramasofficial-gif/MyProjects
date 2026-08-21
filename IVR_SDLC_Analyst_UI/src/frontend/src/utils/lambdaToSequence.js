function sanitizeMermaidName(name) {

    return String(name || "")
        .replace(/[^a-zA-Z0-9_]/g, "_");

}

function getLambdaName(filePath) {

    if (!filePath) {

        return "Lambda";

    }

    const parts =
        filePath.split(/[\\/]/);

    return (
        parts[parts.length - 2] ||
        "Lambda"
    );

}

export function lambdaToSequence(
    content,
    selectedFile
) {

    const lambdaName =
        getLambdaName(selectedFile);

    const calls = [];

    /*
     * Match:
     *
     * await getStatus(...)
     * await service.getStatus(...)
     * await repository.lookup(...)
     */
    const awaitRegex =
        /await\s+([a-zA-Z0-9_.]+)\s*\(/g;

    let match;

    while (
        (match = awaitRegex.exec(content))
        !== null
    ) {

        const original =
            match[1];

        const participant =
            original
                .split(".")
                .pop();

        calls.push({
            participant,
            invocation: original
        });

    }

    const uniqueParticipants =
        [
            ...new Set(
                calls.map(
                    c => c.participant
                )
            )
        ];

    const lines = [];

    lines.push(
        "sequenceDiagram"
    );

    lines.push("");

    lines.push(
        "participant ContactFlow"
    );

    lines.push(
        `participant Lambda as ${lambdaName}`
    );

    lines.push("");

    uniqueParticipants.forEach(
        participant => {

            lines.push(
                `participant ${sanitizeMermaidName(
                    participant
                )}`
            );

        }
    );

    lines.push("");

    lines.push(
        "ContactFlow->>Lambda: Invoke"
    );

    lines.push("");

    calls.forEach(call => {

        const target =
            sanitizeMermaidName(
                call.participant
            );

        lines.push(
            `Lambda->>${target}: ${call.invocation}()`
        );

        lines.push(
            `${target}-->>Lambda: Response`
        );

        lines.push("");

    });

    lines.push(
        "Lambda-->>ContactFlow: Final Response"
    );

    return lines.join("\n");

}