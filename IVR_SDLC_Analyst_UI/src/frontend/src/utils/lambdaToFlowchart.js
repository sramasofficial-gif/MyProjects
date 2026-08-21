export function lambdaToFlowchart(
    content
) {

    const lines = [];

    lines.push(
        "flowchart TD"
    );

    lines.push(
        "Start --> Handler"
    );

    const awaitRegex =
        /await\s+([a-zA-Z0-9_]+)/g;

    let previous =
        "Handler";

    let match;

    while (
        (match = awaitRegex.exec(content))
        !== null
    ) {

        const node =
            match[1];

        lines.push(
            `${previous} --> ${node}`
        );

        previous = node;

    }

    if (previous === "Handler") {

        lines.push(
            'Handler --> SimpleProcessing["Simple Processing"]'
        );

        lines.push(
            "SimpleProcessing --> End"
        );

    }
    else {

        lines.push(
            `${previous} --> End`
        );

    }

    return lines.join("\n");

}