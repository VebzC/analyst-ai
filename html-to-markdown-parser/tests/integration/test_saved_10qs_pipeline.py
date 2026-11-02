import os
from html_to_md.ingestor import convert_full_sec_filing
from logger_config import setup_logger

def test_saved_10q_pipeline():
    setup_logger("logs/test_saved_10q_pipeline.log")

    input_path = "samples/10q_jpm_q3_2024.html"
    assert os.path.exists(input_path), f"Missing input: {input_path}"

    with open(input_path, "r", encoding="utf-8") as f:
        html = f.read()

    output = convert_full_sec_filing(
        html=html,
        base_url="https://dummy.sec.gov/fakepath/",  # won't be used since no exhibits
        output_dir="outputs/test_10q_jpm/"  # output folder
    )

    print("\n--- Markdown Preview (First 1500 chars) ---\n")
    print(output["main_markdown"][:1500])

    # Check basic outputs
    assert "Risk Factors" in output["main_markdown"] or "Management" in output["main_markdown"], "Expected headings not found"
    assert len(output["main_markdown"]) > 2000, "Output too short"
    
    # Check image extraction
    assert isinstance(output["images"], list)
    assert isinstance(output["image_paths"], list)
    print(f"\n✅ Extracted {len(output['images'])} image(s).")
    
    # Check stats dictionary exists and has expected keys
    assert "stats" in output, "Stats dictionary not found in output"
    assert "images_found" in output["stats"], "images_found not found in stats"
    assert "images_processed" in output["stats"], "images_processed not found in stats"
    assert "exhibits_found" in output["stats"], "exhibits_found not found in stats"
    assert "exhibits_processed" in output["stats"], "exhibits_processed not found in stats"
    assert "tree_nodes" in output["stats"], "tree_nodes not found in stats"
    
    # Print stats
    print("\n--- Processing Statistics ---")
    print(f"Images found: {output['stats']['images_found']}")
    print(f"Images processed: {output['stats']['images_processed']}")
    print(f"Exhibits found: {output['stats']['exhibits_found']}")
    print(f"Exhibits processed: {output['stats']['exhibits_processed']}")
    print(f"Tree nodes (estimated): {output['stats']['tree_nodes']}")
    
    # Check exhibit_summaries list (even if empty)
    assert "exhibit_summaries" in output, "exhibit_summaries not found in output"
    if output["exhibit_summaries"]:
        print(f"\n✅ Processed {len(output['exhibit_summaries'])} exhibit(s).")

    print("✅ 10-Q Parsing Test Completed Successfully.")
    print("📄 Markdown saved in: outputs/test_10q_jpm/main.md")
    print("📜 Log saved in: logs/test_saved_10q_pipeline.log") 