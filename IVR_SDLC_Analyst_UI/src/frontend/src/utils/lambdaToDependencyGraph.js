export function lambdaToDependencyGraph(
    content,
    selectedFile
) {

    const imports = [];

    const importRegex =
        /import\s+(.*?)\s+from\s+[^"']+["']/g;

    let match;

    while (
        (match = importRegex.exec(content))
        !== null
    ) {

        imports.push({
            symbol: match[1] || "Unknown",
            module: match[2] || "Unknown"
        });

    }

    const lambdaName =
        selectedFile
            ?.split("/")
            ?.pop()
            || "Lambda";

    const lines = [];

    lines.push("graph LR");

    lines.push(
        `Lambda["${lambdaName}"]`
    );

    imports.forEach(importItem => {

        const target =
            String(
                importItem.module || "Unknown"
            )
            .replace(
                /[^a-zA-Z0-9]/g,
                "_"
            );

        lines.push(
            `Lambda --> ${target}["${importItem.module}"]`
        );

    });

    console.log(
        "IMPORTS FOUND",
        imports
    );
    return lines.join("\n");
}