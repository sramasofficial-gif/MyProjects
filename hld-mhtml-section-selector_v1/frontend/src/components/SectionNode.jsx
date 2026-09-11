import { useMemo, useState } from "react";

const collectIds = (node) => [node.id, ...node.children.flatMap(collectIds)];

export default function SectionNode({ node, selectedIds, onSelectionChange }) {
  const [expanded, setExpanded] = useState(true);
  const descendantIds = useMemo(() => collectIds(node), [node]);
  const selectedCount = descendantIds.filter((id) => selectedIds.has(id)).length;
  const checked = selectedCount === descendantIds.length;
  const indeterminate = selectedCount > 0 && !checked;

  const toggle = () => {
    const next = new Set(selectedIds);
    descendantIds.forEach((id) => (checked ? next.delete(id) : next.add(id)));
    onSelectionChange(next);
  };

  return (
    <li className="section-node">
      <div className="section-row" style={{ "--level": node.level }}>
        {node.children.length > 0 ? (
          <button
            className="chevron"
            type="button"
            onClick={() => setExpanded((value) => !value)}
            aria-label={expanded ? `Collapse ${node.title}` : `Expand ${node.title}`}
          >
            {expanded ? "▾" : "▸"}
          </button>
        ) : (
          <span className="chevron-spacer" />
        )}
        <input
          type="checkbox"
          checked={checked}
          ref={(element) => {
            if (element) element.indeterminate = indeterminate;
          }}
          onChange={toggle}
          id={node.id}
        />
        <label htmlFor={node.id} className="section-label">
          <strong>{node.number ? `${node.number} ` : ""}{node.title}</strong>
          <span className="section-meta">
            Level {node.level}
            {node.page_label ? ` · p.${node.page_label}` : ""}
            {` · ${node.source}`}
          </span>
        </label>
      </div>
      {expanded && node.children.length > 0 && (
        <ul className="section-list section-list--nested">
          {node.children.map((child) => (
            <SectionNode
              key={child.id}
              node={child}
              selectedIds={selectedIds}
              onSelectionChange={onSelectionChange}
            />
          ))}
        </ul>
      )}
    </li>
  );
}
