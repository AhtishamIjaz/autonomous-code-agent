# 👨‍💻 Autonomous Python Code Agent

An intelligent, self-correcting AI agent built with **LangGraph**, **Groq (Llama 3)**, and **Tavily Search**. This agent doesn't just write code—it tests it, identifies errors, researches fixes on the web, and iterates until the code works.

## 🚀 Features
* **Autonomous Iteration**: Loops between writing and testing until the task is successful.
* **Real-time Execution**: Runs Python code locally and captures console output.
* **Web-Powered Debugging**: If an error occurs, the agent uses Tavily Search to find solutions.
* **Streamlit UI**: A clean, interactive dashboard to monitor the agent's "thoughts" and progress.

## 🧠 How it Works (The Logic)
The agent follows a **Stateful Graph** workflow:
1.  **Programmer Node**: Generates Python code using Llama-3-70B.
2.  **Executor Node**: Runs the code and captures the output or stack trace.
3.  **Researcher Node**: (Triggered on error) Searches the internet for a fix.
4.  **Conditional Logic**: The agent retries up to 3 times if errors persist.

## 🛠️ Installation

1. Clone the repo:
   ```bash
   git clone [https://github.com/AhtishamIjaz/autonomous-code-agent.git](https://github.com/AhtishamIjaz/autonomous-code-agent.git)
   cd autonomous-code-agent