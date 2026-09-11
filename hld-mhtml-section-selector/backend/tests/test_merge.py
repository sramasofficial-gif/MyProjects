from app.parsers.extractor import extract_sections,count
def walk(nodes):
    for n in nodes:yield n;yield from walk(n.children)
def test_stale_toc_merge_and_filters():
    html='''<p class="MsoToc1">2.6 Data Governance ........ 10</p><p class="MsoToc2">2.6.2 Data Lifecycle and Retention ........ 12</p><p class="MsoToc2">2.6.3 Metadata Management ........ 13</p><h3>2.6 *Data Governance (Mandatory)*</h3><p style="mso-outline-level:3">2.6.1 Data/Information Ownership &amp; Stewardship</p><h4>2.6.2 Data Lifecycle and Retention</h4><h4>2.6.3 Metadata Management</h4><table><tr><th><h4>Service Name</h4></th></tr></table><div class="diagram"><h4>RBConnectContextDiagram AWS Account TSYS Firewall Open APIs 1a: Call 2b: Route</h4></div>'''
    sections,strategy,warnings=extract_sections(html);nodes=list(walk(sections))
    assert strategy=='merged-toc-and-body';assert [n.number for n in nodes]==['2.6','2.6.1','2.6.2','2.6.3'];assert any('2.6.1' in w for w in warnings);assert all(n.title!='Service Name' for n in nodes)
