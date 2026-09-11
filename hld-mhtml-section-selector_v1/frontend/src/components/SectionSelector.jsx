import SectionNode from "./SectionNode";

const flatten = (nodes) => nodes.flatMap((node) => [node, ...flatten(node.children)]);

export default function SectionSelector({ result, selectedIds, onSelectionChange, onReset }) {
  const allSections = flatten(result.sections);
  const selectedSections = allSections.filter((section) => selectedIds.has(section.id));

  return (
    <section className="selector-card">
      <header className="selector-header">
        <div>
          <p className="eyebrow">Step 1</p>
          <h2>Select sections and review focus</h2>
          <p>
            Check the HLD sections to include in review. Parent selection also selects or clears all child sections.
          </p>
        </div>
        <button type="button" className="button button--secondary" onClick={onReset}>
          Upload another file
        </button>
      </header>

      <div className="document-summary">
        <div><span>Document</span><strong>{result.document_name}</strong></div>
        <div><span>Detected</span><strong>{result.section_count} sections</strong></div>
        <div><span>Strategy</span><strong>{result.detection_strategy}</strong></div>
        <div><span>Selected</span><strong>{selectedIds.size}</strong></div>
      </div>

      {result.warnings.map((warning) => (
        <div className="notice" key={warning}>{warning}</div>
      ))}

      <div className="selector-toolbar">
        <button
          className="text-button"
          type="button"
          onClick={() => onSelectionChange(new Set(allSections.map((section) => section.id)))}
        >
          Select all
        </button>
        <button className="text-button" type="button" onClick={() => onSelectionChange(new Set())}>
          Clear all
        </button>
      </div>

      {result.sections.length > 0 ? (
        <ul className="section-list">
          {result.sections.map((node) => (
            <SectionNode
              key={node.id}
              node={node}
              selectedIds={selectedIds}
              onSelectionChange={onSelectionChange}
            />
          ))}
        </ul>
      ) : (
        <div className="empty-state">
          <h3>No sections detected</h3>
          <p>Apply Word heading styles or add a Table of Contents, export again as MHTML, and retry.</p>
        </div>
      )}

      <footer className="selection-footer">
        <span>{selectedSections.length} of {allSections.length} sections selected</span>
        <button
          type="button"
          className="button button--primary"
          disabled={selectedSections.length === 0}
          onClick={() => window.alert(JSON.stringify({ section_ids: [...selectedIds] }, null, 2))}
        >
          Continue with selected sections
        </button>
      </footer>
    </section>
  );
}
