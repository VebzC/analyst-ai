"""
Simple test for the clean_html function.
"""
from html_to_md.parser import clean_html

def main():
    # Test HTML with style, script, and comments
    test_html = """<html><head><style>body {color: red;}</style></head><body><script>bad()</script><noscript>Enable JS</noscript><p>Hello</p><!-- comment --></body></html>"""
    
    print("Original HTML:")
    print(test_html)
    print("\n" + "-" * 50 + "\n")
    
    # Clean the HTML
    cleaned_html = clean_html(test_html)
    
    print("Cleaned HTML:")
    print(cleaned_html)
    
    # Validation
    checks = [
        ("<style>", "Style tags removed"),
        ("body {color: red;}", "Style content removed"),
        ("<script>", "Script tags removed"),
        ("bad()", "Script content removed"),
        ("<noscript>", "Noscript tags removed"),
        ("Enable JS", "Noscript content removed"),
        ("<!-- comment -->", "Comments removed"),
        ("<p>Hello</p>", "Paragraph content preserved")
    ]
    
    print("\n" + "-" * 50 + "\n")
    print("Validation Results:")
    
    for text, description in checks:
        if text not in cleaned_html:
            result = "PASS"
        else:
            result = "FAIL"
            
        # Special case for content we want to preserve
        if text == "<p>Hello</p>" and text in cleaned_html:
            result = "PASS"
        elif text == "<p>Hello</p>" and text not in cleaned_html:
            result = "FAIL"
            
        print(f"{result}: {description}")

if __name__ == "__main__":
    main() 