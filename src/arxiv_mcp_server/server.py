"""
Arxiv MCP Server
===============

This module implements an MCP (Message Control Protocol) server for interacting with arXiv.
It provides capabilities for searching papers and downloading them as resources.
"""

import logging
import mcp.types as types
from typing import Dict, Any, List
from .config import Settings
from .tools import handle_search, handle_download, handle_list_papers, handle_read_paper
from .tools import search_tool, download_tool, list_tool, read_tool
from .prompts import handle_list_prompts, handle_get_prompt
from .resources import PaperManager
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

# Initialize server settings and paper manager
settings = Settings()
paper_manager = PaperManager()

logger = logging.getLogger("arxiv-mcp-server")
logger.setLevel(logging.INFO)

# Initialize MCP server
server = Server(name=settings.APP_NAME)

# Set up server capabilities
server.capabilities = {
    "prompts": {},  # Enable prompts capability
    "tools": {},    # Enable tools capability
}

@server.list_prompts()
async def list_prompts() -> Dict[str, List[types.Prompt]]:
    """List available prompts."""
    return await handle_list_prompts()


@server.get_prompt()
async def get_prompt(
    name: str, arguments: Dict[str, Any]
) -> Dict[str, List[Dict[str, Any]]]:
    """Get a specific prompt with arguments."""
    return await handle_get_prompt(name, arguments)


@server.list_tools()
async def list_tools() -> List[types.Tool]:
    """List available arXiv research tools."""
    return [
        search_tool,
        download_tool,
        list_tool,
        read_tool,
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls for arXiv research functionality."""
    logger.debug(f"Calling tool {name} with arguments {arguments}")
    try:
        if name == "search_papers":
            return await handle_search(arguments)
        elif name == "download_paper":
            return await handle_download(arguments)
        elif name == "list_papers":
            return await handle_list_papers(arguments)
        elif name == "read_paper":
            return await handle_read_paper(arguments)
        else:
            return [types.TextContent(type="text", text=f"Error: Unknown tool {name}")]
    except Exception as e:
        logger.error(f"Tool error: {str(e)}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the server async context."""
    async with stdio_server() as streams:
        await server.run(
            streams[0],
            streams[1],
            InitializationOptions(
                server_name=settings.APP_NAME,
                server_version=settings.APP_VERSION,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(resources_changed=True),
                    experimental_capabilities={},
                ),
            ),
        )