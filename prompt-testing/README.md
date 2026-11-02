# Prompt Testing with LangChain and LangSmith

A script to test multiple prompt versions against a list of user queries using LangChain and LangSmith.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up your environment variables:
   - Create a `.env` file by copying the template:
     ```
     cp .env.example .env
     ```
   - Edit the `.env` file and add your API keys:
     ```
     OPENAI_API_KEY=your_openai_api_key_here
     LANGCHAIN_API_KEY=your_langsmith_api_key_here
     LANGCHAIN_TRACING_V2=true
     LANGCHAIN_PROJECT=Prompt 1 Eval
     ```

3. Run the script:
   ```
   python prompt_tester.py
   ```

## Features

- Tests 3 different financial analysis prompt versions (v1, v2, v3) against 5 sample queries
- Uses GPT-4 via the OpenAI API
- Logs all runs to LangSmith with prompt version metadata
- Prints responses for each prompt version/query combination to the console
- Organizes results for easy comparison

## Customization

- Edit the `prompt_templates` dictionary in `prompt_tester.py` to test your own prompt versions
- Modify `sample_queries` to test with different queries
- Add or remove prompt versions by updating the dictionary keys and templates

## LangSmith Integration

- All runs are logged to the "Prompt 1 Eval" project in LangSmith
- Metadata includes the prompt version and query ID
- Filter and compare results in the LangSmith UI by prompt version
- View detailed traces in the LangSmith Playground for each run 