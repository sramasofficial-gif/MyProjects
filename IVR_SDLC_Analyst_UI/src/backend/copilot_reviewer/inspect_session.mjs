import {
    CopilotClient
} from "@github/copilot-sdk";

const client = new CopilotClient();

await client.start();

const session =
    await client.createSession();

console.log(
    "Session methods:"
);

console.log(
    Object.getOwnPropertyNames(
        Object.getPrototypeOf(session)
    )
);

console.log(session.registerHooks.toString());
console.log(session.registerTransformCallbacks.toString());
console.log(session.sendAndWait.toString());
console.log(session.getEvents.toString());

await client.stop();