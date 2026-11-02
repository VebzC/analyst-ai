import os
from html_to_md.converter import convert_html_to_markdown

def test_integration_jpm_filing():
    input_path = "samples/jpm_10k_excerpt.html"
    output_path = "outputs/jpm_10k_excerpt.md"

    assert os.path.exists(input_path), f"Missing input file: {input_path}"

    with open(input_path, "r", encoding="utf-8") as f:
        html = f.read()

    markdown = convert_html_to_markdown(html)

    # Print for inspection (optional)
    print("\n--- START MARKDOWN OUTPUT ---\n")
    print(markdown[:2000])  # Limit to first 2k chars
    print("\n--- END MARKDOWN OUTPUT ---\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    # Basic structural checks
    assert "Risk Factors" in markdown or "Management" in markdown, "Missing expected section headings"
    assert "**" in markdown or "*" in markdown, "Expected some formatting to be converted"
    assert len(markdown) > 500, "Output Markdown seems too short"

    print(f"✅ Test complete. Markdown written to: {output_path}")


if __name__ == "__main__":
    test_integration_jpm_filing() 