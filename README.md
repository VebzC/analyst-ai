# Analyst AI: my part

Analyst AI was an AI research assistant for equity research analysts. I co-founded it in 2025 with Neel Patel, building it part-time while I was an equity research associate at Deutsche Bank. The main codebase is public at **https://github.com/patelneel55/analystai**. This repo collects the code I wrote myself.

| Folder | What it is |
|---|---|
| `prototype/` | The first working version, which I built before Neel joined. It's the [first commit in the main repo](https://github.com/patelneel55/analystai/commit/3843f6dc5de8203f2d2632eb1bc591b906aeba10) (24 Mar 2025): a FastAPI app that pulls SEC filings and Polygon market data, analyzes them with LLM calls, and exports financial models to Excel. |
| `early-sec-scripts/` | My first scripts (March 2025): fetch quarterly SEC data, parse XBRL from 10-Qs, turn it into time series, compare financials across periods, and summarize the MD&A section. |
| `html-to-markdown-parser/` | Converts SEC filing HTML into structured Markdown with exhibits split out. I [added it to the main repo](https://github.com/patelneel55/analystai/commit/7f54e32890460f0b19a2491f4fd2297fd3f77707) on 1 Apr 2025. |
| `sec-parser/` | Two ways of turning filings into Markdown, one through sec-api.io and one straight from EDGAR, tested on JPMorgan's 10-Q. |
| `xbrl-parser/` | A pipeline for inline XBRL filings: strip the tags, extract the machine-readable facts, extract headings and tables, and render clean Markdown. On JPMorgan's Q3 2024 10-Q it extracted 7,684 facts across 877 concepts (details in `xbrl-parser/README.md`). |
| `prompt-testing/` | Runs several prompt versions against a list of analyst questions with LangChain and LangSmith, so the answers can be compared side by side. |

After my prototype, Neel rebuilt the system into a production codebase with chunking, vector search, LangGraph agents and layered summaries of long filings. My later work was the filing parsers, the prompts, and defining what a useful answer to an analyst's question looks like.

API keys have been removed. Where a script needs one, set it as an environment variable (see the `.env.example` files).
