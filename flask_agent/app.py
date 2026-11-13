# Free multi-source search agent.
# Tools: DuckDuckGo web/news, Reddit + X (via site: search), Wikipedia. No paid APIs.
# LLM: Groq free tier if GROQ_API_KEY is set (use this for deployment), else local Ollama.

import os
from typing import TypedDict
from urllib.parse import quote

import requests
from dotenv import load_dotenv
from ddgs import DDGS

from langchain.tools import tool
from langchain.agents import create_agent
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from flask import Flask, jsonify, render_template, request

load_dotenv()

UA = {"User-Agent": "gen-search-eng/1.0 (learning project)"}


def _fmt(rows, link_key="href"):
  if not rows:
    return "No results."
  out = []
  for r in rows:
    out.append(
      f"Title: {r.get('title')}\nLink: {r.get(link_key)}\nSnippet: {r.get('body', '')}"
    )
  return "\n\n".join(out)[:8000]


def _ddg_text(q, n=6):
  try:
    return _fmt(DDGS().text(q, max_results=n))
  except Exception as e:  # return the error to the agent instead of crashing the run
    return f"Search failed: {e}"


@tool(description="General web search (DuckDuckGo). Use first for most questions.")
def web_search(query: str) -> str:
  print("Web search is being used...")
  return _ddg_text(query)


@tool(description="Recent news search. Use for current events and latest developments.")
def news_search(query: str) -> str:
  print("News search is being used...")
  try:
    return _fmt(DDGS().news(query, max_results=6), link_key="url")
  except Exception as e:
    return f"Search failed: {e}"


@tool(description="Search Reddit discussions and opinions.")
def reddit_search(query: str) -> str:
  print("Reddit is being used...")
  return _ddg_text(f"site:reddit.com {query}")


@tool(description="Search X (Twitter) posts and profiles.")
def x_search(query: str) -> str:
  print("X is being used...")
  return _ddg_text(f"site:x.com {query}")


@tool(description="Look up background/encyclopedic info on a person, place, concept or company (Wikipedia).")
def wikipedia_search(query: str) -> str:
  print("Wikipedia is being used...")
  try:
    r = requests.get(
      "https://en.wikipedia.org/w/api.php",
      params={"action": "query", "list": "search", "srsearch": query, "srlimit": 3, "format": "json"},
      headers=UA, timeout=15,
    )
    hits = r.json()["query"]["search"]
    if not hits:
      return "No Wikipedia results."
    out = []
    for h in hits:
      title = h["title"]
      s = requests.get(
        f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title.replace(' ', '_'))}",
        headers=UA, timeout=15,
      )
      if s.status_code != 200:
        continue
      j = s.json()
      link = j.get("content_urls", {}).get("desktop", {}).get("page", "")
      out.append(f"Title: {title}\nLink: {link}\nSummary: {j.get('extract', '')}")
    return "\n\n".join(out) or "No Wikipedia results."
  except Exception as e:
    return f"Wikipedia lookup failed: {e}"


def get_llm():
  if os.getenv("GROQ_API_KEY"):
    from langchain_groq import ChatGroq
    return ChatGroq(model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"), temperature=0)
  return ChatOllama(model=os.getenv("OLLAMA_MODEL", "qwen2.5:3b"), temperature=0)


SYSTEM_PROMPT = (
  "Only state numbers, dates, names and claims that appear in the tool results. "
  "If a detail is not in the results, leave it out rather than guessing. "
  "Do not repeat a search with a near-identical query; call each tool at most twice. "
)

agent = create_agent(
  model=get_llm(),
  tools=[web_search, news_search, wikipedia_search, reddit_search, x_search],
  system_prompt=SYSTEM_PROMPT,
)


class State(TypedDict, total=False):
  query: str
  answer: str


def agent_node(state: State) -> State:
  result = agent.invoke(
    {"messages": [("human", state["query"])]},
    config={"recursion_limit": 12},
  )
  return {"answer": result["messages"][-1].content}


graph = StateGraph(State)
graph.add_node("agent", agent_node)
graph.set_entry_point("agent")
graph.add_edge("agent", END)

langgraph_app = graph.compile()
flask_app = Flask(__name__)


@flask_app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if request.is_json:
            query = request.get_json(silent=True).get("query", "").strip()
            if not query:
                return jsonify({"error": "No query provided"}), 400

            answer = langgraph_app.invoke({"query": query})["answer"]
            return jsonify({"answer": answer})

        query = request.form.get("query", "").strip()
        if not query:
            return render_template("index.html", error="Please enter a query")

        answer = langgraph_app.invoke({"query": query})["answer"]
        return render_template("index.html", query=query, answer=answer)

    return render_template("index.html")


if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=5000, debug=True)
