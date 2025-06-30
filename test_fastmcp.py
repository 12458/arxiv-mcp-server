#!/usr/bin/env python3
"""Test script for the FastMCP arXiv server."""

import asyncio
from fastmcp import Client
from src.arxiv_mcp_server.server import mcp


async def test_server():
    """Test the FastMCP server functionality."""
    print("Testing FastMCP arXiv server...")
    
    # Connect to the server using in-memory transport
    async with Client(mcp) as client:
        # Test listing tools
        tools = await client.list_tools()
        print(f"Available tools: {[tool.name for tool in tools]}")
        
        # Test search functionality
        print("\nTesting search_papers...")
        result = await client.call_tool("search_papers", {
            "query": "machine learning",
            "max_results": 3
        })
        print(f"Search result: {result.text[:200]}...")
        
        # Test prompt functionality
        print("\nTesting deep_paper_analysis prompt...")
        prompt_result = await client.get_prompt("deep_paper_analysis", {
            "paper_id": "2301.12345",
            "expertise_level": "intermediate"
        })
        print(f"Prompt result: {prompt_result.text[:200]}...")


if __name__ == "__main__":
    asyncio.run(test_server()) 