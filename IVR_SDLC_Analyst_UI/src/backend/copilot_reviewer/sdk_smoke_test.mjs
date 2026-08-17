import {
    CopilotClient
} from "@github/copilot-sdk";

let client = null;
let session = null;

try {
    console.log(
        "Creating CopilotClient..."
    );

    client = new CopilotClient();

    console.log(
        "Starting Copilot client..."
    );

    await client.start();

    console.log(
        "Copilot client started."
    );

    console.log(
        "Creating session..."
    );

    session =
        await client.createSession();

    console.log(
        "Session created."
    );

    const response =
        await session.sendAndWait({
            prompt: [
                "Return only valid JSON.",
                "",
                "Use exactly this structure:",
                '{"status":"ok","message":"Copilot SDK is working"}'
            ].join("\n")
        });

    console.log(
        "Raw response:"
    );

    console.dir(
        response,
        {
            depth: 10,
            colors: true
        }
    );

} catch (error) {
    console.error(
        "Copilot SDK smoke test failed:"
    );

    console.error(error);

    process.exitCode = 1;

} finally {
    if (
        session &&
        typeof session.destroy === "function"
    ) {
        try {
            await session.destroy();

            console.log(
                "Session destroyed."
            );
        } catch (error) {
            console.error(
                "Session cleanup failed:",
                error
            );
        }
    }

    if (
        client &&
        typeof client.stop === "function"
    ) {
        try {
            await client.stop();

            console.log(
                "Copilot client stopped."
            );
        } catch (error) {
            console.error(
                "Client cleanup failed:",
                error
            );
        }
    }
}