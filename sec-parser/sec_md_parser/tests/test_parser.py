from sec_md_parser import SECParser

def test_parser_init():
    parser = SECParser()
    assert parser is not None
    assert hasattr(parser, "metadata_extractor")
    assert hasattr(parser, "document_parser")
    assert hasattr(parser, "xbrl_parser")

def test_html_to_markdown():
    parser = SECParser()
    html = "<html><head><title>Test</title></head><body><h1>Hello</h1><p>World</p></body></html>"
    markdown = parser.html_to_markdown(html, include_xbrl=False)
    assert "Hello" in markdown
    assert "World" in markdown
