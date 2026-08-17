// inspect_models.mjs

import {
    CopilotClient
} from "@github/copilot-sdk";

const client = new CopilotClient();

await client.start();

console.log(
    await client.listModels()
);

await client.stop();