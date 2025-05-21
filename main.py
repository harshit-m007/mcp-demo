import arxiv
import json
import os
from typing import List
from mcp.server.fastmcp import FastMCP


PAPER_DIR = "papers"

# GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
# MODEL_NAME = "gemma-7b-it"  # Or "mixtral-8x7b-32768", "llama2-70b-4096"

mcp = FastMCP("research", port = 8001)
@mcp.tool()
def search_papers(topic: str, max_results: int = 5) -> List[str]:
    """Search for papers on arXiv based on a topic and store their information.
    Args:
    topic:The topic to search for 
    max_results:Maximum number of results to ritieve(default: 5)
    
    Returns:
    List of paper IDs found in the search"""
    client = arxiv.Client()
    search = arxiv.Search(
        query=topic, 
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )
    
    papers = client.results(search)
    path = os.path.join(PAPER_DIR, topic.lower().replace(" ", "_"))
    os.makedirs(path, exist_ok=True)
    
    file_path = os.path.join(path, "papers_info.json")
    try:
        with open(file_path, "r") as json_file:
            papers_info = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        papers_info = {}
        
    paper_ids = []
    for paper in papers:
        paper_ids.append(paper.get_short_id())
        papers_info[paper.get_short_id()] = {
            'title': paper.title,
            'authors': [author.name for author in paper.authors],
            'summary': paper.summary,
            'pdf_url': paper.pdf_url,
            'published': str(paper.published.date())
        }
    
    with open(file_path, "w") as json_file:
        json.dump(papers_info, json_file, indent=2)
        
    return paper_ids

@mcp.tool()
def extract_info(paper_id: str) -> str:
    """Search for information about a specific paper across all topic directories.
        Args:
            paper_id: THe ID of the paper to look for
        
        Returns:
        JSON string with paper information if found, error message if not found"""
    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)
        if os.path.isdir(item_path):
            file_path = os.path.join(item_path, "papers_info.json")
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r") as json_file:
                        papers_info = json.load(json_file)
                        if paper_id in papers_info:
                            return json.dumps(papers_info[paper_id], indent=2)
                except (FileNotFoundError, json.JSONDecodeError):
                    continue
    return f"Paper {paper_id} not found."

# def call_groq_api(messages: list, tools: list = None):
#     """Call Groq's API with the given messages and tools."""
#     headers = {
#         "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
#         "Content-Type": "application/json"
#     }
    
#     payload = {
#         "model": MODEL_NAME,
#         "messages": messages,
#         "temperature": 0.7
#     }
    
#     if tools:
#         payload["tools"] = tools
    
#     response = requests.post(GROQ_API_URL, headers=headers, json=payload)
#     return response.json()

# def process_query(query: str):
#     """Process a user query using Groq's API with function calling."""
#     messages = [{"role": "user", "content": query}]
    
#     while True:
#         response = call_groq_api(messages, tools)
#         message = response["choices"][0]["message"]
#         messages.append(message)
        
#         if "tool_calls" not in message:
#             return message["content"]
        
#         for tool_call in message["tool_calls"]:
#             tool_name = tool_call["function"]["name"]
#             tool_args = json.loads(tool_call["function"]["arguments"])
#             print(f"Calling {tool_name} with {tool_args}")
            
#             result = execute_tool(tool_name, tool_args)
#             messages.append({
#                 "role": "tool",
#                 "name": tool_name,
#                 "content": result,
#                 "tool_call_id": tool_call["id"]
#             })

# def execute_tool(tool_name: str, tool_args: dict):
#     """Execute a tool and return the result."""
#     if tool_name == "search_papers":
#         return json.dumps(search_papers(**tool_args))
#     elif tool_name == "extract_info":
#         return extract_info(**tool_args)
#     return "Unknown tool"

# tools = [
#     {
#         "type": "function",
#         "function": {
#             "name": "search_papers",
#             "description": "Search for papers on arXiv",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "topic": {"type": "string"},
#                     "max_results": {"type": "integer", "default": 5}
#                 },
#                 "required": ["topic"]
#             }
#         }
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "extract_info",
#             "description": "Get information about a specific paper",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "paper_id": {"type": "string"}
#                 },
#                 "required": ["paper_id"]
#             }
#         }
#     }
# ]

if __name__ == "__main__":

    
    mcp.run(transport='sse')