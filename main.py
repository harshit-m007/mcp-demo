import arxiv
import json
import os
from typing import List
from mcp.server.fastmcp import FastMCP


PAPER_DIR = "papers"


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


if __name__ == "__main__":

    
    mcp.run(transport='sse')