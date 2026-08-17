// inspect_auth.mjs

import {
    CopilotClient
} from "@github/copilot-sdk";

const client = new CopilotClient();

await client.start();

console.log(
    await client.getAuthStatus()
);

await client.stop();