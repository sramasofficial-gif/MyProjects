from app.parsers.section_extractor import extract_sections, count_sections

def titles(nodes): return [n.title for n in nodes for n in ([n]+[x for c in n.children for x in walk(c)])]
def walk(n):
    yield n
    for c in n.children: yield from walk(c)

def test_filters_table_and_diagram():
    html='''<h2>2.0 Solution Architecture</h2><h3>2.1 Project Context</h3><div class="diagram"><h4>RBConnectContextDiagram CDE AWS Account TSYS Firewall Open APIs TCS Portal PCI use cases: 1. Get A 2. Set B 3. Verify C</h4></div><h4>2.1.1 In-Scope Applications</h4><h3>2.2 Application Communication</h3><h4>1991 � � RBCONNECT � � ACD Customer Amazon Connect 1b: Send Email 2b: Route</h4><h3>2.3 Enterprise Services</h3><table><tr><th><h4>Service Name</h4></th><th><h4>Producing Application</h4></th></tr></table>'''
    sections,strategy,_=extract_sections(html); all_titles=[n.title for root in sections for n in walk(root)]
    assert strategy=="filtered-html-headings" and count_sections(sections)==5
    assert "Service Name" not in all_titles and not any("RBConnect" in x for x in all_titles)

def test_toc_authoritative():
    html='''<p class="MsoToc1">2.0 Solution Architecture ........ 4</p><p class="MsoToc2">2.1 Project Context ........ 5</p><h2>2.0 Solution Architecture</h2><table><tr><th><h4>Service Name</h4></th></tr></table>'''
    sections,strategy,_=extract_sections(html)
    assert strategy=="table-of-contents" and count_sections(sections)==2 and sections[0].page_label=="4"
