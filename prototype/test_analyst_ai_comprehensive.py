"""
Comprehensive Test for Analyst AI

This script tests all major components of the Analyst AI system:
1. SEC filing retrieval
2. Text extraction from PDFs
3. Keyword searching in filings
4. Financial metrics retrieval
5. LLM analysis pipeline
"""

import os
import sys
import time
import logging
from typing import Dict, Any, List, Optional

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Try to read API key from .env file if not set in environment
if not os.environ.get('OPENAI_API_KEY'):
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    key = line.strip().split('=', 1)[1].strip('"').strip("'")
                    os.environ['OPENAI_API_KEY'] = key
                    break
    except Exception as e:
        logger.error(f"Could not read OpenAI API key from .env file: {e}")

# Import tool modules
from tools.get_sec_filing import get_sec_filing
from tools.sec_preprocessor import extract_text_from_pdf
from tools.sec_keyword_searcher import search_filing_for_keywords
from tools.analyze_keyword_matches import summarize_keyword_matches
from tools.tighten_llm_insight import tighten_llm_insight
from tools.get_financial_metric import get_financial_metric

# Import LLM and registry modules
try:
    from planner_llm import plan_tool_call
    from tool_registry import run_tool
    from analyzer_llm import analyze_tool_output
    HAS_LLM_MODULES = True
except ImportError:
    logger.warning("LLM modules not found, some tests will be skipped")
    HAS_LLM_MODULES = False


def test_sec_filing_retrieval() -> bool:
    """Test SEC filing retrieval for Apple."""
    logger.info("Testing SEC filing retrieval...")
    
    try:
        # Get the most recent 10-K filing for Apple
        result = get_sec_filing("AAPL", "10-K")
        
        if "error" in result:
            logger.error(f"Error retrieving SEC filing: {result['error']}")
            return False
        
        logger.info(f"Successfully retrieved SEC filing:")
        logger.info(f"  Ticker: {result['ticker']}")
        logger.info(f"  Form: {result['form_type']}")
        logger.info(f"  Date: {result['filing_date']}")
        logger.info(f"  PDF Path: {result['pdf_path']}")
        
        # Verify the PDF file exists
        if not os.path.exists(result['pdf_path']):
            logger.error(f"PDF file not found at path: {result['pdf_path']}")
            return False
            
        return True
    
    except Exception as e:
        logger.error(f"Exception in SEC filing retrieval: {str(e)}", exc_info=True)
        return False


def test_pdf_text_extraction(pdf_path: Optional[str] = None) -> bool:
    """Test text extraction from a PDF file."""
    logger.info("Testing PDF text extraction...")
    
    try:
        # Use the provided path or find a PDF in the cache
        if pdf_path is None:
            # Try to find a PDF in the cache directory
            cache_dir = "cache/sec_filings"
            for root, dirs, files in os.walk(cache_dir):
                for file in files:
                    if file.endswith(".pdf"):
                        pdf_path = os.path.join(root, file)
                        break
                if pdf_path:
                    break
                    
        if not pdf_path or not os.path.exists(pdf_path):
            logger.error(f"No PDF file found for text extraction test")
            return False
            
        logger.info(f"Extracting text from PDF: {pdf_path}")
        pages = extract_text_from_pdf(pdf_path)
        
        if not pages or len(pages) == 0:
            logger.error("No text extracted from PDF")
            return False
            
        logger.info(f"Successfully extracted text from {len(pages)} pages")
        logger.info(f"First page preview: {pages[0][:200]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"Exception in PDF text extraction: {str(e)}", exc_info=True)
        return False


def test_keyword_searching(pages: Optional[List[str]] = None, pdf_path: Optional[str] = None) -> bool:
    """Test keyword searching functionality."""
    logger.info("Testing keyword searching...")
    
    try:
        # If pages not provided, try to extract from a PDF
        if pages is None and pdf_path:
            pages = extract_text_from_pdf(pdf_path)
        
        # If still no pages, report failure
        if not pages or len(pages) == 0:
            logger.error("No text available for keyword searching test")
            return False
            
        # Define some keywords to search for
        keywords = [
            "revenue", 
            "growth", 
            "risk", 
            "competition", 
            "profit", 
            "margin"
        ]
        
        logger.info(f"Searching for keywords: {', '.join(keywords)}")
        matches = search_filing_for_keywords(pages, keywords, window=100)
        
        if not matches or len(matches) == 0:
            logger.warning("No keyword matches found")
            return False
            
        logger.info(f"Found {len(matches)} keyword matches")
        # Print a sample match
        if matches:
            logger.info(f"Sample match - Keyword: {matches[0]['keyword']}")
            logger.info(f"Sample context: {matches[0]['context'][:100]}...")
            
        return True
        
    except Exception as e:
        logger.error(f"Exception in keyword searching: {str(e)}", exc_info=True)
        return False


def test_financial_metrics() -> bool:
    """Test financial metrics retrieval."""
    logger.info("Testing financial metrics retrieval...")
    
    try:
        # Test retrieving basic company metrics
        tickers = ["AAPL", "MSFT", "JPM"]
        metrics = ["revenue", "net_income", "pe_ratio", "market_cap"]
        
        success_count = 0
        
        for ticker in tickers:
            for metric in metrics:
                logger.info(f"Retrieving {metric} for {ticker}...")
                result = get_financial_metric(ticker=ticker, metric=metric)
                
                if "error" in result:
                    logger.warning(f"Error retrieving {metric} for {ticker}: {result['error']}")
                    continue
                    
                logger.info(f"{ticker} {metric}: {result['value']}")
                success_count += 1
                
        # Consider the test successful if at least half of the metric retrievals worked
        success_rate = success_count / (len(tickers) * len(metrics))
        logger.info(f"Financial metrics success rate: {success_rate:.2%}")
        
        return success_rate >= 0.5
        
    except Exception as e:
        logger.error(f"Exception in financial metrics retrieval: {str(e)}", exc_info=True)
        return False


def test_llm_pipeline() -> bool:
    """Test the full LLM pipeline with a simple query."""
    if not HAS_LLM_MODULES:
        logger.warning("Skipping LLM pipeline test - modules not available")
        return False
        
    logger.info("Testing LLM pipeline...")
    
    try:
        # Test query
        query = "What is the market cap of Apple?"
        
        # Step 1: Plan the tool call
        logger.info(f"Planning tool call for query: '{query}'")
        plan = plan_tool_call(query)
        
        if "tool" not in plan or plan.get("tool") == "error":
            logger.error(f"Tool planning failed: {plan}")
            return False
            
        logger.info(f"Planned tool: {plan['tool']}")
        logger.info(f"Planned args: {plan['args']}")
        
        # Step 2: Execute the tool
        logger.info("Executing planned tool...")
        result = run_tool(plan['tool'], plan['args'])
        
        if "error" in result:
            logger.error(f"Tool execution failed: {result['error']}")
            return False
            
        logger.info(f"Tool execution result: {result}")
        
        # Step 3: Analyze the result
        logger.info("Analyzing tool result...")
        analysis = analyze_tool_output(result, query)
        
        logger.info(f"Analysis: {analysis}")
        
        return True
        
    except Exception as e:
        logger.error(f"Exception in LLM pipeline: {str(e)}", exc_info=True)
        return False


def test_sec_analysis_pipeline() -> bool:
    """Test the SEC filing analysis pipeline."""
    logger.info("Testing SEC analysis pipeline...")
    
    try:
        # Step 1: Get an SEC filing
        filing_result = get_sec_filing("AAPL", "10-K")
        
        if "error" in filing_result:
            logger.error(f"Error retrieving SEC filing: {filing_result['error']}")
            return False
            
        pdf_path = filing_result['pdf_path']
        
        # Step 2: Extract text from the PDF
        logger.info(f"Extracting text from {pdf_path}")
        pages = extract_text_from_pdf(pdf_path)
        
        if not pages or len(pages) == 0:
            logger.error("No text extracted from PDF")
            return False
            
        # Step 3: Search for keywords
        keywords = [
            "revenue", 
            "growth", 
            "profit", 
            "competition", 
            "risk",
            "technology"
        ]
        
        logger.info(f"Searching for keywords: {', '.join(keywords)}")
        matches = search_filing_for_keywords(pages, keywords, window=100)
        
        if not matches or len(matches) == 0:
            logger.warning("No keyword matches found")
            return False
            
        # Step 4: Summarize keyword matches
        logger.info("Summarizing keyword matches...")
        summary = summarize_keyword_matches(
            matches, 
            original_query="What are the key revenue drivers and risks for Apple?"
        )
        
        logger.info(f"Summary: {summary[:200]}...")
        
        # Step 5: Tighten the summary
        logger.info("Tightening summary...")
        tightened = tighten_llm_insight(summary)
        
        logger.info(f"Tightened summary: {tightened[:200]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"Exception in SEC analysis pipeline: {str(e)}", exc_info=True)
        return False


def main():
    """Run all tests and report results."""
    logger.info("=== Starting Comprehensive Analyst AI Test ===")
    
    results = {}
    
    # Test 1: SEC Filing Retrieval
    results["SEC Filing Retrieval"] = test_sec_filing_retrieval()
    
    # Store the PDF path if retrieval succeeded
    pdf_path = None
    sec_filing_result = get_sec_filing("AAPL", "10-K")
    if "error" not in sec_filing_result and "pdf_path" in sec_filing_result:
        pdf_path = sec_filing_result["pdf_path"]
    
    # Test 2: PDF Text Extraction
    results["PDF Text Extraction"] = test_pdf_text_extraction(pdf_path)
    
    # Extract pages for keyword searching if we have a PDF
    pages = None
    if pdf_path:
        try:
            pages = extract_text_from_pdf(pdf_path)
        except:
            pass
    
    # Test 3: Keyword Searching
    results["Keyword Searching"] = test_keyword_searching(pages, pdf_path)
    
    # Test 4: Financial Metrics
    results["Financial Metrics"] = test_financial_metrics()
    
    # Test 5: LLM Pipeline
    if HAS_LLM_MODULES:
        results["LLM Pipeline"] = test_llm_pipeline()
    else:
        results["LLM Pipeline"] = False
        logger.warning("LLM Pipeline test skipped - modules not available")
    
    # Test 6: SEC Analysis Pipeline
    results["SEC Analysis Pipeline"] = test_sec_analysis_pipeline()
    
    # Report results
    logger.info("\n=== Test Results ===")
    
    all_passed = True
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
        
        if not result:
            all_passed = False
    
    # Overall result
    if all_passed:
        logger.info("\n✅ ALL TESTS PASSED - System is working seamlessly!")
        return 0
    else:
        logger.info("\n❌ SOME TESTS FAILED - See logs for details")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 