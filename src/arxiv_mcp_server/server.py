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


# @server.list_resources()
# async def list_resources() -> List[types.Resource]:
#     """List available paper resources."""
#     logger.info("Listing resources")
#     resources = await paper_manager.list_resources()
#     logger.info(f"Found {len(resources)} resources")
#     return resources


# @server.read_resource()
# async def read_resource(uri: AnyUrl) -> str:
#     """Read the content of a paper resource."""
#     assert uri.path is not None
#     paper_id = Path(uri.path).stem
#     return await paper_manager.get_paper_content(paper_id)


# @server.set_logging_level()
# async def set_logging_level(level: types.LoggingLevel) -> types.EmptyResult:
#     """Set the server logging level."""
#     logger.setLevel(level.upper())
#     await server.request_context.session.send_log_message(
#         level="debug", data=f"Log level set to {level}", logger="arxiv-mcp-server"
#     )
#     return types.EmptyResult()


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
