// MyProjects/IVR_SDLC_Analyst_UI/src/backend/copilot_reviewer/review_lambda.mjs

// ... keep all your existing readStandardInput, createReviewPrompt, normalizeReview helper functions exactly as they are ...
import process from "node:process";
import { CopilotClient, RuntimeConnection } from "@github/copilot-sdk";


async function readStandardInput() {
    let input = "";

    for await (const chunk of process.stdin) {
        input += chunk;
    }

    if (!input.trim()) {
        throw new Error(
            "No review request was supplied."
        );
    }

    return JSON.parse(input);
}


function createReviewPrompt({
    relativePath,
    source
}) {
    return `
Review the following AWS Lambda TypeScript source file.

File:
${relativePath}

Perform an evidence-based source-code review covering:

1. Correctness and likely defects
2. AWS Lambda handler implementation
3. Error handling
4. Logging and observability
5. Input validation
6. TypeScript type safety
7. Security
8. Reliability
9. Performance
10. Maintainability
11. Testability
12. AWS SDK usage
13. Timeout, retry, and failure behavior

Return only valid JSON.

Do not use Markdown code fences.
Do not include text before or after the JSON object.

Return exactly this structure:

{
  "summary": "Short summary of the review",
  "overallRisk": "Low | Medium | High",
  "recommendations": [
    {
      "id": "REC-001",
      "severity": "Critical | High | Medium | Low | Info",
      "category": "Correctness | Security | Reliability | Performance | Maintainability | Testing | Observability | Type Safety",
      "line": 0,
      "title": "Short recommendation title",
      "finding": "What was observed in the source",
      "recommendation": "A specific actionable recommendation"
    }
  ]
}

Rules:

- Use line 0 if a precise line cannot be determined.
- Do not invent behavior that is not visible in the source.
- Do not claim a security vulnerability unless supported by the source.
- Keep recommendations concise and actionable.
- Return an empty recommendations array if no findings exist.

Source code:

${source}
`.trim();
}


function extractResponseText(response) {
    if (typeof response === "string") {
        return response;
    }

    if (
        response &&
        typeof response.content === "string"
    ) {
        return response.content;
    }

    if (
        response &&
        typeof response.message?.content === "string"
    ) {
        return response.message.content;
    }

    if (
        response &&
        typeof response.data?.content === "string"
    ) {
        return response.data.content;
    }

    throw new Error(
        "Copilot returned an unsupported response format."
    );
}


function normalizeReview(rawText) {
    const cleanedText = rawText
        .trim()
        .replace(/^```json\s*/i, "")
        .replace(/^```\s*/i, "")
        .replace(/\s*```$/i, "");

    const parsed = JSON.parse(cleanedText);

    if (
        !parsed ||
        typeof parsed !== "object" ||
        Array.isArray(parsed)
    ) {
        throw new Error(
            "Copilot review is not a JSON object."
        );
    }

    const recommendations =
        Array.isArray(parsed.recommendations)
            ? parsed.recommendations
            : [];

    return {
        summary:
            typeof parsed.summary === "string"
                ? parsed.summary
                : "",

        overallRisk:
            typeof parsed.overallRisk === "string"
                ? parsed.overallRisk
                : "Unknown",

        recommendations:
            recommendations.map(
                (item, index) => ({
                    id:
                        item?.id ||
                        `REC-${String(
                            index + 1
                        ).padStart(3, "0")}`,

                    severity:
                        item?.severity || "Info",

                    category:
                        item?.category ||
                        "Maintainability",

                    line:
                        Number.isFinite(
                            Number(item?.line)
                        )
                            ? Number(item.line)
                            : 0,

                    title:
                        item?.title ||
                        "Recommendation",

                    finding:
                        item?.finding || "",

                    recommendation:
                        item?.recommendation || ""
                })
            )
    };
}


function writeResult(result) {
    process.stdout.write(
        `${JSON.stringify(result)}\n`
    );
}

async function main() {
    let client = null;
    let session = null;

    try {
        const request = await readStandardInput();

        if (
            typeof request.relativePath !== "string" ||
            typeof request.source !== "string"
        ) {
            throw new Error("relativePath and source are required.");
        }

        // --- FIXED: PROGRAMMATICALLY RESOLVE AND INJECT TOKEN TO THE SDK CONSTRUCTOR ---
        // Dynamically looks at standard system environment profiles passed down from Python
        //const secureToken = process.env.COPILOT_GITHUB_TOKEN || process.env.GITHUB_TOKEN;
        //const secureToken = " [REDACTED_GITHUB_PAT]";
        const secureToken =
            process.env.COPILOT_GITHUB_TOKEN ??
            process.env.GITHUB_TOKEN;

        //if (!secureToken) {
        //    throw new Error(
        //        "Authentication failed: The target Copilot Token is empty or missing valid corporate credentials. Check server.py configuration environments."
        //    );
        //}

        console.error(
            "Token length:",
            secureToken?.length || 0
        );

        console.error(
            "Mode:",
            "Explicit Token Authentication"
        );

        // Pass an explicit configuration parameters mapping block to initialize the authentication provider
        client = new CopilotClient({
            connection: RuntimeConnection.forStdio(),
            //env: {
            //    ...process.env,
            //    COPILOT_GITHUB_TOKEN: secureToken,
            //    GITHUB_TOKEN: secureToken
            //},
            useLoggedInUser: true // Disables looking for IDE login flags
        });
        console.error("Client created");
        // --- END OF FIX ---

        console.error("Environment check:");
        console.error(
            "COPILOT_GITHUB_TOKEN:",
            !!process.env.COPILOT_GITHUB_TOKEN
        );

        console.error(
            "GITHUB_TOKEN:",
            !!process.env.GITHUB_TOKEN
        );

        console.error(
            "USERPROFILE:",
            process.env.USERPROFILE
        );

        console.error(
            "APPDATA:",
            process.env.APPDATA
        );

        console.error(
            "HOME:",
            process.env.HOME
        );
        console.error("Starting client");
        await client.start();
        console.error("Client started");

        console.error("Creating session");
        session = await client.createSession({
            systemMessage: {
                content:
                    "You are a senior TypeScript and AWS Lambda code reviewer. Return structured, evidence-based findings."
            }
        });
        console.error("Session created");

        const response = await session.sendAndWait({
            prompt: createReviewPrompt(request)
        });

        const responseText = extractResponseText(response);
        const normalizedReview = normalizeReview(responseText);

        writeResult({
            success: true,
            file: request.relativePath,
            ...normalizedReview
        });
    } catch (error) {
        writeResult({
            success: false,
            error: "copilot_review_failed",
            message:
                error instanceof Error
                    ? error.message
                    : String(error)
                });

        process.exitCode = 1;
    } finally {
        if (session && typeof session.destroy === "function") {
            try { await session.destroy(); } catch {}
        }
        if (client) {
            try { await client.stop(); } catch {}
        }
    }
}

await main();
