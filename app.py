import streamlit as st
import os
import io
import sys
from typing import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults

# 1. SETUP & THEME
load_dotenv()
st.set_page_config(page_title="Pro AI Code Agent", layout="wide", page_icon="🚀")

# Beautiful Custom CSS
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #FF4B4B; color: white; }
    .stTextArea>div>div>textarea { font-family: 'Courier New', Courier, monospace; }
    .agent-update { padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #ff4b4b; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. API KEYS
GROQ_KEY = os.getenv("GROQ_API_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")

if not GROQ_KEY or not TAVILY_KEY:
    st.error("Missing API Keys! Please check your .env file.")
    st.stop()

# 3. AGENT DEFINITION
class AgentState(TypedDict):
    task: str
    code: str
    error: str
    research: str
    iterations: int
    output: str

llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0, groq_api_key=GROQ_KEY)
search_tool = TavilySearchResults(max_results=1, tavily_api_key=TAVILY_KEY)

# --- NODES ---
def programmer_node(state: AgentState):
    st.info(f"🤖 **Programmer**: Drafting code (Attempt {state['iterations'] + 1})")
    prompt = f"""Task: {state['task']}
    Instruction: Write ONLY raw Python code. 
    - Use the 'requests' library if needed.
    - DO NOT use markdown blocks like ```python.
    - DO NOT include conversational text.
    - If there was an error: {state['error']}
    - Use this research: {state['research']}
    
    IMPORTANT: Print the final result clearly."""
    
    response = llm.invoke(prompt)
    # Force removal of markdown just in case
    clean_code = response.content.replace("```python", "").replace("```", "").strip()
    return {"code": clean_code, "iterations": state['iterations'] + 1}

def executor_node(state: AgentState):
    st.info("⚙️ **Executor**: Running script...")
    old_stdout = sys.stdout
    redirected_output = io.StringIO()
    sys.stdout = redirected_output
    
    try:
        exec(state['code'], globals())
        captured = redirected_output.getvalue()
        sys.stdout = old_stdout
        st.success(f"✅ **Success!**")
        return {"error": "None", "output": captured}
    except Exception as e:
        sys.stdout = old_stdout
        err_msg = str(e)
        st.error(f"❌ **Error detected**: {err_msg}")
        return {"error": err_msg, "output": ""}

def researcher_node(state: AgentState):
    st.warning("🔍 **Researcher**: Investigating the fix...")
    
    # FIX: Sanitize the error to prevent Tavily 400 Bad Request
    error_summary = str(state['error']).split('\n')[-1][:120]
    query = f"python fix error {error_summary}"
    
    try:
        results = search_tool.invoke({"query": query})
        return {"research": str(results)}
    except:
        return {"research": "Check syntax and indentation carefully."}

# --- GRAPH ---
builder = StateGraph(AgentState)
builder.add_node("programmer", programmer_node)
builder.add_node("executor", executor_node)
builder.add_node("researcher", researcher_node)
builder.add_edge(START, "programmer")
builder.add_edge("programmer", "executor")

def check_result(state: AgentState):
    return "end" if state['error'] == "None" or state['iterations'] >= 3 else "retry"

builder.add_conditional_edges("executor", check_result, {"end": END, "retry": "researcher"})
builder.add_edge("researcher", "programmer")
app_engine = builder.compile()

# 4. FRONTEND UI
st.title("👨‍💻 Autonomous Python Agent")
st.subheader("I write, test, and debug code until it works.")

with st.sidebar:
    st.header("Configuration")
    task_input = st.text_area("What should I code?", 
                             "Get the price of Bitcoin in USD from CoinGecko API and print it.")
    max_tries = st.slider("Max Debugging Loops", 1, 5, 3)
    st.markdown("---")
    if st.button("Clear History"):
        st.rerun()

if st.button("Start Agent"):
    with st.container():
        inputs = {"task": task_input, "code": "", "error": "None", "research": "", "iterations": 0, "output": ""}
        
        with st.spinner("Agent is thinking..."):
            final_result = app_engine.invoke(inputs)
        
        st.divider()
        st.header("🏁 Final Results")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Console Output")
            st.code(final_result['output'] if final_result['output'] else "No output.")
            
        with col2:
            st.subheader("Generated Code")
            st.code(final_result['code'], language='python')