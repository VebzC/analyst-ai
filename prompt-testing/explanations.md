# Prompt Testing Script Explanation

## Filename: prompt_tester.py

## Purpose
This script tests multiple prompt template versions against a set of user queries using LangChain and LangSmith. It allows easy comparison of different prompt formulations by running each prompt version against the same set of test queries and logging the results for analysis.

## Functions and Classes

### test_prompts_with_queries(prompt_templates, queries)
- **Purpose**: Loops through each prompt version and each query, runs the query through the prompt chain, and logs results to LangSmith
- **Inputs**: 
  - `prompt_templates`: Dictionary mapping version names to prompt templates
  - `queries`: List of string queries to test
- **Outputs**: List of dictionaries with prompt_version, query, and response
- **Logic**: Nested loop that first iterates through prompt versions, then through queries, running each combination with proper metadata

## Key Logic Decisions

1. **Environment Variables from .env**: Uses python-dotenv to load API keys and configuration from a .env file
   ```python
   load_dotenv()
   ```

2. **Required Environment Validation**: Checks that all required API keys are present before running
   ```python
   required_env_vars = ["OPENAI_API_KEY", "LANGCHAIN_API_KEY"]
   missing_vars = [var for var in required_env_vars if not os.getenv(var)]
   if missing_vars:
       raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
   ```

3. **Prompt Dictionary Structure**: Stores multiple prompt versions in a dictionary for easy iteration and identification
   ```python
   prompt_templates = {
       "v1": "...",
       "v2": "...",
       "v3": "..."
   }
   ```

4. **Chain Creation Inside Loop**: Creates a new chain for each prompt version to isolate the processing
   ```python
   for version, template in prompt_templates.items():
       prompt = PromptTemplate.from_template(template)
       chain = ({"query": RunnablePassthrough()} | prompt | model | StrOutputParser())
   ```

5. **LangSmith Metadata**: Adds version metadata to each trace for better analysis and filtering in LangSmith
   ```python
   with langsmith.trace(
       name=f"{version} - Query {i}",
       metadata={"prompt_version": version, "query_id": i}
   ):
   ```

6. **Structured Results Collection**: Maintains comprehensive results with version info for later analysis
   ```python
   results.append({
       "prompt_version": version,
       "query": query, 
       "response": response
   })
   ```

7. **LangSmith Configuration**: Sets up LangSmith for tracing and project organization
   ```python
   os.environ["LANGCHAIN_TRACING_V2"] = "true"
   os.environ["LANGCHAIN_PROJECT"] = "Prompt 1 Eval"
   ```

8. **Zero Temperature**: Sets temperature to 0 for maximum determinism in testing
   ```python
   model = ChatOpenAI(model="gpt-4", temperature=0)
   ```

## Best Practices and Alternatives

1. **Alternative Approach**: Could have used LangChain's Evaluation framework to automatically score responses from different prompt versions

2. **Prompt A/B Testing**: This implements a basic form of prompt A/B testing, which could be extended with quantitative metrics

3. **Performance Consideration**: For large prompt sets or many queries, could implement batching or parallelization

4. **Analysis Enhancements**: Could add code to analyze and compare response characteristics (length, sentiment, specificity) across versions

5. **Environment Management**: Using python-dotenv provides a more secure and portable way to manage API keys than hardcoding in the script

6. **Error Handling**: Added validation for required environment variables to catch configuration issues early 