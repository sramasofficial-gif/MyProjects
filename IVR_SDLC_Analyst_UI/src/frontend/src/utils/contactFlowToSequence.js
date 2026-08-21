const MAX_ACTIONS = 80;

const ACTION_LABELS = {
    InvokeLambdaFunction:
        "Invoke Lambda",

    MessageParticipant:
        "Play prompt",

    GetParticipantInput:
        "Collect caller input",

    StoreCustomerInput:
        "Collect caller input",

    SetAttributes:
        "Set contact attributes",

    UpdateContactAttributes:
        "Update contact attributes",

    CheckAttribute:
        "Evaluate attribute",

    Compare:
        "Evaluate condition",

    TransferContactToQueue:
        "Transfer to queue",

    TransferContactToFlow:
        "Transfer to flow",

    TransferContactToAgent:
        "Transfer to agent",

    ConnectParticipantWithLexBot:
        "Invoke Lex bot",

    ConnectParticipantWithLexBotV2:
        "Invoke Lex bot",

    DisconnectParticipant:
        "Disconnect caller",

    EndFlowExecution:
        "End flow",

    UpdateContactTargetQueue:
        "Set target queue",

    SetRecordingBehavior:
        "Configure recording",

    SetLoggingBehavior:
        "Configure logging",

    Wait:
        "Wait",

    Loop:
        "Loop"
};

function sanitizeMermaidText(value) {
    return String(value ?? "")
        .replaceAll("\r", " ")
        .replaceAll("\n", " ")
        .replaceAll(":", " -")
        .replaceAll(";", ",")
        .replaceAll('"', "'")
        .replace(/\s+/g, " ")
        .trim();
}

function createSafeAlias(value, index) {
    const normalized =
        String(value ?? "")
            .replace(/[^a-zA-Z0-9_]/g, "_")
            .replace(/^(\d)/, "_$1");

    return normalized || `Participant_${index}`;
}

function lastArnSegment(value) {
    if (
        typeof value !== "string" ||
        value.length === 0
    ) {
        return "";
    }

    const sections = value.split(/[:/]/);

    return sections[sections.length - 1] || value;
}

function findStringByKey(
    object,
    acceptedKeys
) {
    if (
        !object ||
        typeof object !== "object"
    ) {
        return "";
    }

    for (const [key, value] of Object.entries(object)) {
        if (
            acceptedKeys.includes(
                key.toLowerCase()
            ) &&
            typeof value === "string"
        ) {
            return value;
        }

        if (
            value &&
            typeof value === "object"
        ) {
            const nested =
                findStringByKey(
                    value,
                    acceptedKeys
                );

            if (nested) {
                return nested;
            }
        }
    }

    return "";
}

function getActionDisplayName(action) {
    const metadataName =
        action?.Metadata?.ActionMetadata?.Name ||
        action?.Metadata?.name ||
        action?.Metadata?.Name;

    if (metadataName) {
        return sanitizeMermaidText(metadataName);
    }

    return (
        ACTION_LABELS[action?.Type] ||
        sanitizeMermaidText(action?.Type) ||
        "Contact flow action"
    );
}

function getIntegration(action) {
    const type = action?.Type || "";
    const parameters = action?.Parameters || {};

    if (type === "InvokeLambdaFunction") {
        const functionArn =
            findStringByKey(
                parameters,
                [
                    "functionarn",
                    "lambdaarn",
                    "function"
                ]
            );

        return {
            kind: "lambda",
            displayName:
                lastArnSegment(functionArn) ||
                "AWS Lambda",
            request:
                getActionDisplayName(action),
            response:
                "Lambda result"
        };
    }

    if (
        type.includes("LexBot") ||
        type.includes("Lex")
    ) {
        const botName =
            findStringByKey(
                parameters,
                [
                    "botname",
                    "botaliasarn",
                    "botarn"
                ]
            );

        return {
            kind: "lex",
            displayName:
                lastArnSegment(botName) ||
                "Amazon Lex",
            request:
                getActionDisplayName(action),
            response:
                "Bot response"
        };
    }

    if (
        type === "TransferContactToQueue" ||
        type === "UpdateContactTargetQueue"
    ) {
        const queue =
            findStringByKey(
                parameters,
                [
                    "queueid",
                    "queuearn",
                    "queue"
                ]
            );

        return {
            kind: "queue",
            displayName:
                lastArnSegment(queue) ||
                "Target Queue",
            request:
                getActionDisplayName(action),
            response: ""
        };
    }

    if (type === "TransferContactToFlow") {
        const targetFlow =
            findStringByKey(
                parameters,
                [
                    "contactflowid",
                    "contactflowarn",
                    "flowid",
                    "flowarn"
                ]
            );

        return {
            kind: "flow",
            displayName:
                lastArnSegment(targetFlow) ||
                "Target Flow",
            request:
                getActionDisplayName(action),
            response: ""
        };
    }

    return null;
}

function getTransitionTargets(action) {
    const transitions =
        action?.Transitions || {};

    const targets = [];

    if (transitions.NextAction) {
        targets.push({
            kind: "next",
            label: "Next",
            target: transitions.NextAction
        });
    }

    for (
        const condition of
        transitions.Conditions || []
    ) {
        if (condition?.NextAction) {
            targets.push({
                kind: "condition",
                label:
                    sanitizeMermaidText(
                        condition?.Condition?.Operator ||
                        condition?.Condition?.ComparisonValue ||
                        condition?.Condition ||
                        "Condition matched"
                    ),
                target: condition.NextAction
            });
        }
    }

    for (
        const errorTransition of
        transitions.Errors || []
    ) {
        if (errorTransition?.NextAction) {
            targets.push({
                kind: "error",
                label:
                    sanitizeMermaidText(
                        errorTransition.ErrorType ||
                        "Error"
                    ),
                target:
                    errorTransition.NextAction
            });
        }
    }

    return targets;
}

function orderActions(flow) {
    const actions =
        Array.isArray(flow?.Actions)
            ? flow.Actions
            : [];

    if (actions.length === 0) {
        return [];
    }

    const actionById =
        new Map(
            actions.map(action => [
                action.Identifier,
                action
            ])
        );

    const ordered = [];
    const visited = new Set();

    function visit(actionId) {
        if (
            !actionId ||
            visited.has(actionId) ||
            ordered.length >= MAX_ACTIONS
        ) {
            return;
        }

        const action =
            actionById.get(actionId);

        if (!action) {
            return;
        }

        visited.add(actionId);
        ordered.push(action);

        const transitions =
            getTransitionTargets(action);

        const normalTransitions =
            transitions.filter(
                item => item.kind !== "error"
            );

        const errorTransitions =
            transitions.filter(
                item => item.kind === "error"
            );

        for (const transition of [
            ...normalTransitions,
            ...errorTransitions
        ]) {
            visit(transition.target);
        }
    }

    visit(flow.StartAction);

    for (const action of actions) {
        visit(action.Identifier);
    }

    return ordered;
}

export function contactFlowToSequenceDiagram(
    content,
    selectedFile
) {
    let flow;

    try {
        flow =
            typeof content === "string"
                ? JSON.parse(content)
                : content;
    } catch {
        throw new Error(
            "The selected file does not contain valid JSON."
        );
    }

    if (
        !flow ||
        !Array.isArray(flow.Actions)
    ) {
        throw new Error(
            "The JSON does not contain an Amazon Connect Actions array."
        );
    }

    const flowName =
        sanitizeMermaidText(
            flow?.Metadata?.name ||
            flow?.Name ||
            selectedFile
                ?.split(/[\\/]/)
                .pop()
                ?.replace(/\.json$/i, "") ||
            "Contact Flow"
        );

    const orderedActions =
        orderActions(flow);

    const integrations = [];
    const integrationAliases = new Map();

    for (const action of orderedActions) {
        const integration =
            getIntegration(action);

        if (!integration) {
            continue;
        }

        const key =
            `${integration.kind}:${integration.displayName}`;

        if (!integrationAliases.has(key)) {
            const alias =
                createSafeAlias(
                    integration.displayName,
                    integrations.length
                );

            integrationAliases.set(key, alias);

            integrations.push({
                ...integration,
                key,
                alias
            });
        }
    }

    const lines = [
        "sequenceDiagram",
        "    autonumber",
        "    actor Caller",
        `    participant Flow as ${flowName}`
    ];

    for (const integration of integrations) {
        lines.push(
            `    participant ${integration.alias} as ${
                sanitizeMermaidText(
                    integration.displayName
                )
            }`
        );
    }

    lines.push(
        "",
        "    Caller->>Flow: Start contact flow",
        "    activate Flow"
    );

    for (const action of orderedActions) {
        const actionLabel =
            getActionDisplayName(action);

        const integration =
            getIntegration(action);

        if (integration) {
            const key =
                `${integration.kind}:${integration.displayName}`;

            const alias =
                integrationAliases.get(key);

            lines.push(
                `    Flow->>${alias}: ${
                    sanitizeMermaidText(
                        integration.request
                    )
                }`
            );

            if (integration.response) {
                lines.push(
                    `    ${alias}-->>Flow: ${
                        sanitizeMermaidText(
                            integration.response
                        )
                    }`
                );
            }

            continue;
        }

        const type = action?.Type || "";

        if (
            type === "MessageParticipant" ||
            type === "GetParticipantInput" ||
            type === "StoreCustomerInput"
        ) {
            lines.push(
                `    Flow->>Caller: ${actionLabel}`
            );

            if (
                type === "GetParticipantInput" ||
                type === "StoreCustomerInput"
            ) {
                lines.push(
                    "    Caller-->>Flow: Input"
                );
            }

            continue;
        }

        if (
            type === "DisconnectParticipant" ||
            type === "EndFlowExecution"
        ) {
            lines.push(
                `    Flow-->>Caller: ${actionLabel}`
            );
            continue;
        }

        const transitions =
            getTransitionTargets(action);

        const conditional =
            transitions.filter(
                item =>
                    item.kind === "condition" ||
                    item.kind === "error"
            );

        if (conditional.length > 0) {
            lines.push(
                `    Note over Flow: ${actionLabel}`
            );

            conditional.forEach(
                (transition, index) => {
                    const keyword =
                        index === 0
                            ? "alt"
                            : "else";

                    lines.push(
                        `    ${keyword} ${
                            sanitizeMermaidText(
                                transition.label
                            )
                        }`,
                        `        Flow->>Flow: Route to ${
                            sanitizeMermaidText(
                                transition.target
                            )
                        }`
                    );
                }
            );

            lines.push("    end");
            continue;
        }

        lines.push(
            `    Flow->>Flow: ${actionLabel}`
        );
    }

    lines.push(
        "    deactivate Flow",
        "    Flow-->>Caller: Complete interaction"
    );

    return lines.join("\n");
}