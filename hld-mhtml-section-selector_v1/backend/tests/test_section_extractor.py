from app.parsers.section_extractor import count_sections, extract_sections


def test_html_heading_tree():
    html = """
    <html><body>
      <h1>1 Architecture</h1>
      <h2>1.1 Components</h2>
      <h2>1.2 Interfaces</h2>
      <h1>2 Security</h1>
    </body></html>
    """
    sections, strategy, warnings = extract_sections(html)
    assert strategy == "html-headings"
    assert warnings == []
    assert count_sections(sections) == 4
    assert sections[0].title == "Architecture"
    assert sections[0].children[0].title == "Components"
    assert sections[1].title == "Security"


def test_word_heading_style():
    html = """
    <html><body>
      <p class="MsoHeading1">Overview</p>
      <p class="MsoHeading2">Scope</p>
    </body></html>
    """
    sections, strategy, _ = extract_sections(html)
    assert strategy == "word-heading-styles"
    assert sections[0].children[0].title == "Scope"


def test_numbered_paragraph_fallback():
    html = """
    <html><body>
      <p>1 Introduction</p>
      <p>1.1 Purpose</p>
      <p>This is normal paragraph content and should not be selected.</p>
    </body></html>
    """
    sections, strategy, _ = extract_sections(html)
    assert strategy == "numbered-paragraphs"
    assert count_sections(sections) == 2
