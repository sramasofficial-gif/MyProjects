# Copilot reviewer change required for actual visual review

The Python backend now sends `visualReviewRequired` and `visualEvidence` in each review packet. The existing `copilot_reviewer/generate_diagram.mjs` must pass those files to the GitHub Copilot SDK message as attachments.

The current GitHub Copilot SDK supports image attachments by absolute file path:

```js
const attachments = (input.visualReviewRequired && Array.isArray(input.visualEvidence))
  ? input.visualEvidence
      .filter(v => v && v.path)
      .map(v => ({
          type: "file",
          path: v.path,
          displayName: v.displayName || "hld-visual.png",
      }))
  : [];

const response = await session.sendAndWait({
  prompt,
  attachments,
});
```

If the reviewer already calls `session.send(...)`, use the same `attachments` property there.

The prompt should explicitly tell the model that visual attachments are available and must be inspected when `visualReviewRequired` is true, for example:

```js
const visualInstruction = input.visualReviewRequired
  ? `\nVISUAL REVIEW REQUIRED: Inspect every attached HLD image/diagram. Use the actual visual relationships, boundaries, labels, arrows, components, and connectors as evidence. Do not treat OCR/flattened text as a substitute for the image.`
  : "";

const prompt = `${basePrompt}${visualInstruction}`;
```

A useful structured result field is:

```json
{
  "visual_review": {
    "performed": true,
    "components_observed": [],
    "relationships_observed": [],
    "visual_findings": []
  }
}
```

Do not mark `performed: true` unless an image attachment was actually supplied to the model.
