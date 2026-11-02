"""
Example script to convert an HTML file to Markdown.
"""
from convert_file import convert_html_file_to_markdown

# Path to the HTML file in the samples directory
html_file_path = "samples/10q_jpm_q3_2024.html"

# Convert the HTML file to Markdown and get the result
markdown_result = convert_html_file_to_markdown(html_file_path)

# Save the result to a file for inspection
output_file_path = "outputs/10q_jpm_q3_2024.md"
with open(output_file_path, 'w', encoding='utf-8') as f:
    f.write(markdown_result)

print(f"Conversion complete! Output saved to {output_file_path}")

# Print the first 500 characters of the result
print("\nPreview of the converted Markdown:")
print("-" * 50)
preview = markdown_result[:500]
print(preview + "..." if len(markdown_result) > 500 else preview)
print("-" * 50) 