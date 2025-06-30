"""Tool definitions for the arXiv MCP server."""

from .search import handle_search
from .download import handle_download
from .list_papers import handle_list_papers
from .read_paper import handle_read_paper


__all__ = [
    "handle_search",
    "handle_download",
    "handle_read_paper",
    "handle_list_papers",
]
