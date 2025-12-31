import os
from typing import TypedDict
from dotenv import load_dotenv  # <--- This is the key for .env files
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults

# 1. LOAD API KEYS FROM .ENV
load_dotenv() 

GROQ_KEY = os.getenv("GROQ_API_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")

# 2. DEFINE STATE
class AgentState(TypedDict):
    task: str
    code: str
    error: str
    research: str
    iterations: int

# 3. INITIALIZE MODELS
# We pass the keys directly here or let LangChain find them in the environment
llm = ChatGroq(
    model_name="llama-3.3-70b-versatile", 
    temperature=0,
    groq_api_key=GROQ_KEY
)
search_tool = TavilySearchResults(
    max_results=1,
    tavily_api_key=TAVILY_KEY
)

# 4. NODES (The Logic)
def programmer_node(state: AgentState):
    print(f"\n🤖 [PROGRAMMER] Creating script (Attempt {state['iterations'] + 1})...")
    prompt = f"""Task: {state['task']}
    Instruction: Write raw Python code. Use requests.
    The Binance API returns: {{"symbol":"BTCUSDT","price":"96000.00"}}.
    You MUST print the price result using print().
    Existing Research: {state['research']}"""
    response = llm.invoke(prompt)
    return {"code": response.content, "iterations": state['iterations'] + 1}

def executor_node(state: AgentState):
    print("⚙️ [EXECUTOR] Testing code...")
    # Clean the code from markdown backticks
    code = state['code'].replace("```python", "").replace("```", "").strip()
    try:
        # Warning: exec() is powerful; use only with trusted LLM output
        exec(code, globals())
        return {"error": "None"}
    except Exception as e:
        print(f"❌ Run Error: {e}")
        return {"error": str(e)}

def researcher_node(state: AgentState):
    print("🔍 [RESEARCHER] Finding solution...")
    query = f"python binance api price keyerror {state['error']}"
    results = search_tool.invoke({"query": query})
    return {"research": str(results)}

# 5. GRAPH SETUP
builder = StateGraph(AgentState)
builder.add_node("programmer", programmer_node)
builder.add_node("executor", executor_node)
builder.add_node("researcher", researcher_node)

builder.add_edge(START, "programmer")
builder.add_edge("programmer", "executor")

def check_result(state: AgentState):
    if state['error'] == "None" or state['iterations'] >= 3:
        return "end"
    return "retry"

builder.add_conditional_edges(
    "executor", 
    check_result, 
    {"end": END, "retry": "researcher"}
)
builder.add_edge("researcher", "programmer")
app = builder.compile()

# 6. EXECUTION
if __name__ == "__main__":
    inputs = {
        "task": "Use requests to get https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd. Print data['bitcoin']['usd'].",
        "code": "",
        "error": "None",
        "research": "None",
        "iterations": 0
    }

    print("🚀 STARTING AGENT...")
    final_state = app.invoke(inputs)
    print("\n✅ DONE. FINAL CODE GENERATED:")
    print("-" * 30)
    print(final_state['code'])
    print("-" * 30)