"""
Arxiv MCP Server
===============

This module implements an MCP server for interacting with arXiv using FastMCP.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from fastmcp import FastMCP, Context
from .config import Settings
from .tools import handle_search, handle_download, handle_list_papers, handle_read_paper
from .prompts.handlers import list_prompts as handler_list_prompts
from .prompts.handlers import get_prompt as handler_get_prompt

settings = Settings()
logger = logging.getLogger("arxiv-mcp-server")
logger.setLevel(logging.INFO)

# Create FastMCP server instance
mcp = FastMCP(settings.APP_NAME, version=settings.APP_VERSION)

@mcp.tool
async def search_papers(
    query: str,
    max_results: int = 10,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    categories: Optional[List[str]] = None,
    ctx: Optional[Context] = None
) -> str:
    """Search for papers on arXiv with advanced filtering.
    
    Args:
        query (required, str): Search query string
        max_results (optional, int): Maximum number of results to return (default: 10)
        date_from (optional, str): Start date for filtering (YYYY-MM-DD format)
        date_to (optional, str): End date for filtering (YYYY-MM-DD format)
        categories (optional, list[str]): List of arXiv categories to filter by
    
    Returns:
        JSON string containing search results
    """
    if ctx:
        await ctx.info(f"Searching for papers with query: {query}")
    
    arguments = {
        "query": query,
        "max_results": max_results,
        "categories": categories or []
    }
    
    # Only add date filters if they are not None
    if date_from is not None:
        arguments["date_from"] = date_from
    if date_to is not None:
        arguments["date_to"] = date_to
    
    result = await handle_search(arguments)
    return result[0] if result else "No results found"


@mcp.tool
async def download_paper(
    paper_id: str,
    check_status: bool = False,
    ctx: Optional[Context] = None
) -> str:
    """Download a paper from arXiv by ID.
    
    Args:
        paper_id: The arXiv paper ID (e.g., '2301.12345')
        check_status: If true, only check conversion status without downloading
        ctx: FastMCP context for logging and other features
    
    Returns:
        JSON string containing download information
    """
    if ctx:
        await ctx.info(f"Downloading paper: {paper_id}")
    
    arguments = {"paper_id": paper_id, "check_status": check_status}
    result = await handle_download(arguments)
    return result[0] if result else "Download failed"


@mcp.tool
async def list_papers(
    ctx: Optional[Context] = None
) -> str:
    """List recently downloaded papers.
    
    Args:
        ctx: FastMCP context for logging and other features
    
    Returns:
        JSON string containing list of papers
    """
    if ctx:
        await ctx.info("Listing downloaded papers")
    
    arguments = {}
    result = await handle_list_papers(arguments)
    return result[0] if result else "No papers found"


@mcp.tool
async def read_paper(
    paper_id: str,
    ctx: Optional[Context] = None
) -> str:
    """Read and extract text content from a downloaded paper.
    
    Args:
        paper_id: The arXiv paper ID (e.g., '2301.12345')
        ctx: FastMCP context for logging and other features
    
    Returns:
        JSON string containing paper content
    """
    if ctx:
        await ctx.info(f"Reading paper: {paper_id}")
    
    arguments = {"paper_id": paper_id}
    result = await handle_read_paper(arguments)
    return result[0] if result else "Failed to read paper"


@mcp.prompt
async def deep_paper_analysis(
    paper_id: str,
    expertise_level: str = "intermediate",
    analysis_focus: str = "general",
    ctx: Optional[Context] = None
) -> str:
    """Generate a deep analysis prompt for a specific paper.
    
    Args:
        paper_id: The arXiv paper ID to analyze
        expertise_level: Target expertise level (beginner, intermediate, expert)
        analysis_focus: Specific aspect to focus on (general, methodology, results, etc.)
        ctx: FastMCP context for logging and other features
    
    Returns:
        Formatted prompt string for paper analysis
    """
    if ctx:
        await ctx.info(f"Generating analysis prompt for paper: {paper_id}")
    
    arguments = {
        "paper_id": paper_id,
        "expertise_level": expertise_level,
        "analysis_focus": analysis_focus
    }
    
    try:
        result = await handler_get_prompt("deep-paper-analysis", arguments)
        return result
    except Exception as e:
        logger.error(f"Error generating prompt: {str(e)}")
        return f"Error generating analysis prompt: {str(e)}"


def main():
    """Run the FastMCP server."""
    mcp.run(transport="http", host="127.0.0.1", port=8000, path="/mcp")


if __name__ == "__main__":
    main()
