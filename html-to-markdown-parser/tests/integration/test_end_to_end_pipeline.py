import os
import unittest.mock
from html_to_md.ingestor import convert_full_sec_filing
from html_to_md.converter import convert_html_to_markdown  # Import the markdown converter directly
from logger_config import setup_logger

def test_full_pipeline_end_to_end():
    # Setup logging
    log_path = "logs/full_pipeline.log"
    setup_logger(log_path)

    # Input HTML
    input_path = "samples/full_8k_with_exhibits.html"
    assert os.path.exists(input_path), f"Missing test input: {input_path}"

    with open(input_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Create mock exhibits
    mock_exhibits = []
    
    # Load exhibit files from samples directory
    exhibit_files = [
        {
            "title": "Exhibit 3.1 - Certificate of Designations",
            "file": "samples/exhibit_3_1.html"
        },
        {
            "title": "Exhibit 4.1 - Form of Certificate",
            "file": "samples/exhibit_4_1.html"
        }
    ]
    
    for exhibit_info in exhibit_files:
        if os.path.exists(exhibit_info["file"]):
            with open(exhibit_info["file"], "r", encoding="utf-8") as f:
                html_content = f.read()
                
                # Pre-convert to markdown so we can verify it works
                markdown_content = convert_html_to_markdown(html_content)
                
                mock_exhibits.append({
                    "title": exhibit_info["title"],
                    "url": f"file://{os.path.abspath(exhibit_info['file'])}",
                    "html": html_content,
                    "markdown": markdown_content
                })
    
    # If we don't have exhibit files, use a fallback mock
    if not mock_exhibits:
        html_content = """
        <html>
        <head><title>Mock Exhibit</title></head>
        <body>
            <h1>Mock Exhibit Content</h1>
            <p>This is a mock exhibit for testing when no sample exhibits are available.</p>
            <h2>Section 1: Introduction</h2>
            <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam auctor, nisl eget ultricies aliquam, 
            nunc nisl aliquet nunc, vitae aliquam nisl nunc vitae nisl. Nulla facilisi. Nulla facilisi.</p>
            <h2>Section 2: Details</h2>
            <p>Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, 
            totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.</p>
        </body>
        </html>
        """
        markdown_content = convert_html_to_markdown(html_content)
        mock_exhibits.append({
            "title": "Mock Exhibit",
            "url": "file:///mock/exhibit.html",
            "html": html_content,
            "markdown": markdown_content
        })

    # Combine all the patches we need
    with unittest.mock.patch('html_to_md.ingestor.parse_exhibit_links') as mock_parse_links, \
         unittest.mock.patch('html_to_md.ingestor.fetch_exhibits') as mock_fetch_exhibits:
        
        # Make the parse_exhibit_links return a list of dictionaries with titles and URLs
        mock_links = [{"title": ex["title"], "url": ex["url"]} for ex in mock_exhibits]
        mock_parse_links.return_value = mock_links
        
        # Make fetch_exhibits return our mock exhibits
        mock_fetch_exhibits.return_value = mock_exhibits
        
        # Run the pipeline
        output = convert_full_sec_filing(
            html=html,
            base_url="file:///samples/",
            output_dir="outputs/full_test/"  # Save everything
        )

    # Verify main document
    assert "main_markdown" in output
    assert isinstance(output["main_markdown"], str)
    assert len(output["main_markdown"]) > 1000, "Markdown output too short"

    print("\n--- Markdown Preview (First 1000 chars) ---\n")
    print(output["main_markdown"][:1000])

    # Verify exhibits
    assert "exhibits" in output
    assert isinstance(output["exhibits"], list)
    assert len(output["exhibits"]) == len(mock_exhibits), f"Expected {len(mock_exhibits)} exhibits, got {len(output['exhibits'])}"
    
    # Verify each exhibit
    successful_exhibits = 0
    for exhibit in output["exhibits"]:
        assert "title" in exhibit
        assert "markdown" in exhibit
        
        # Verify markdown content length
        if len(exhibit["markdown"]) > 100:
            successful_exhibits += 1
            print(f"✅ Exhibit processed successfully: {exhibit['title'][:60]}...")
        else:
            print(f"⚠️ Exhibit has short markdown: {exhibit['title'][:60]}...")

    print(f"\n📊 Results: {successful_exhibits}/{len(output['exhibits'])} exhibits processed successfully.")
    print(f"📄 Output written to: outputs/full_test/main.md")
    print(f"📂 Images saved in: outputs/full_test/images/")
    print(f"📂 Exhibits saved in: outputs/full_test/exhibits/")
    print(f"📜 Log file: {log_path}")

    assert os.path.exists(log_path)
    assert successful_exhibits > 0, "No exhibits were processed successfully" 