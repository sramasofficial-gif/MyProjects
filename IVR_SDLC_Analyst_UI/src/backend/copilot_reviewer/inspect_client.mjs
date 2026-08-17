import {
    CopilotClient
} from "@github/copilot-sdk";

const client = new CopilotClient();

console.log(
    Object.getOwnPropertyNames(
        Object.getPrototypeOf(client)
    )
);