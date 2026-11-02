"""
Prompt testing script using LangChain and LangSmith.
Tests multiple prompt versions against multiple user queries using OpenAI's GPT-4.
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import langsmith

# Load environment variables from .env file
load_dotenv()

# Verify that required API keys are set
required_env_vars = ["OPENAI_API_KEY", "LANGCHAIN_API_KEY"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}. "
                     f"Please add them to your .env file.")

# LangSmith Configuration
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "Prompt 1 Eval"

# Confirm LangSmith setup
print(f"LangSmith tracing enabled for project: {os.getenv('LANGCHAIN_PROJECT')}")

# Create multiple versions of "Prompt 1"
prompt_templates = {
    "v1": """You are a financial analysis assistant.
Your goal is to provide concise, accurate information about companies and markets.

User Query: {query}

Please respond with a well-structured analysis based on the query above.
Keep your response under 200 words and focus on the most relevant information.
""",
    
    "v2": """You are an expert equity research analyst with 20 years of experience.
Provide factual, data-driven insights about markets and companies.

User Query: {query}

Your response should:
- Be concrete and specific
- Include key metrics when relevant
- Avoid speculation
- Stay under 200 words
""",
    
    "v3": """As a financial advisor to institutional investors, your analysis must be:
- Rigorous and evidence-based
- Focused on long-term implications
- Balanced with pros and cons

User Query: {query}

Provide your expert assessment in a concise format (max 200 words).
"""
}

# Initialize the LLM
model = ChatOpenAI(model="gpt-4", temperature=0)

# Sample user queries
sample_queries = [
    "What are the key financial metrics to look at for tech companies?",
    "Explain the P/E ratio and why it matters for value investing.",
    "How do rising interest rates affect bank stocks?",
    "What should I look for in a company's cash flow statement?",
    "Compare and contrast fundamental analysis vs technical analysis."
]

# Run each query through each prompt version and log to LangSmith
def test_prompts_with_queries(prompt_templates, queries):
    results = []
    
    print("Testing multiple prompt versions with sample queries...\n")
    
    for version, template in prompt_templates.items():
        print(f"===== TESTING PROMPT VERSION: {version} =====\n")
        
        # Initialize the prompt for this version
        prompt = PromptTemplate.from_template(template)
        
        # Create the chain for this prompt version
        chain = (
            {"query": RunnablePassthrough()} 
            | prompt 
            | model 
            | StrOutputParser()
        )
        
        for i, query in enumerate(queries, 1):
            print(f"Query {i}: {query}")
            
            # Execute the chain with tracing enabled and metadata
            with langsmith.trace(
                name=f"{version} - Query {i}",
                metadata={"prompt_version": version, "query_id": i}
            ):
                response = chain.invoke(query)
            
            results.append({
                "prompt_version": version,
                "query": query, 
                "response": response
            })
            
            print(f"Response ({version}):\n{response}\n")
            print("-" * 80 + "\n")
        
        print("\n")
    
    print(f"All {len(results)} combinations processed. View detailed results in LangSmith project: 'Prompt 1 Eval'")
    return results

if __name__ == "__main__":
    test_prompts_with_queries(prompt_templates, sample_queries) 