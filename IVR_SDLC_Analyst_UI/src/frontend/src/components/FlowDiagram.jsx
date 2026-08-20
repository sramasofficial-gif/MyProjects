import ReactFlow from "reactflow";

export default function FlowDiagram({
    nodes,
    edges
}) {

    return (
        <div
            style={{
                height: "700px"
            }}
        >

            <ReactFlow
                nodes={nodes}
                edges={edges}
                fitView
            />

        </div>
    );
}