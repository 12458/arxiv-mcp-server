[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/12458/arxiv-mcp-server/actions/workflows/tests.yml/badge.svg)](https://github.com/blazickjp/arxiv-mcp-server/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI Downloads](https://img.shields.io/pypi/dm/arxiv-mcp-server.svg)](https://pypi.org/project/arxiv-mcp-server/)
[![PyPI Version](https://img.shields.io/pypi/v/arxiv-mcp-server.svg)](https://pypi.org/project/arxiv-mcp-server/)

# ArXiv MCP Server

> 🔍 Enable AI assistants to search and access arXiv papers through a simple MCP interface.

The ArXiv MCP Server provides a bridge between AI assistants and arXiv's research repository through the Model Context Protocol (MCP). Built with FastMCP v2 for optimal performance and developer experience, it allows AI models to search for papers and access their content in a programmatic way.

<div align="center">
  
🤝 **[Contribute](https://github.com/12458/arxiv-mcp-server/blob/main/CONTRIBUTING.md)** • 
📝 **[Report Bug](https://github.com/12458/arxiv-mcp-server/issues)**

<a href="https://www.pulsemcp.com/servers/blazickjp-arxiv-mcp-server"><img src="https://www.pulsemcp.com/badge/top-pick/blazickjp-arxiv-mcp-server" width="400" alt="Pulse MCP Badge"></a>
</div>

## ✨ Core Features

- 🔎 **Paper Search**: Query arXiv papers with filters for date ranges and categories
- 📄 **Paper Access**: Download and read paper content
- 📋 **Paper Listing**: View all downloaded papers
- 🗃️ **Local Storage**: Papers are saved locally for faster access
- 📝 **Prompts**: A Set of Research Prompts
- ⚡ **FastMCP v2**: Built with the latest FastMCP framework for optimal performance
- 🔧 **Multiple Transports**: Support for STDIO, HTTP, and SSE transports
- 🛡️ **Type Safety**: Automatic schema generation from Python type hints

## 🚀 Quick Start

### Installing via Smithery

To install ArXiv Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/arxiv-mcp-server):

```bash
npx -y @smithery/cli install arxiv-mcp-server --client claude
```

### Installing Manually
Install using uv:

```bash
uv tool install arxiv-mcp-server
```

For development:

```bash
# Clone and set up development environment
git clone https://github.com/12458/arxiv-mcp-server.git
cd arxiv-mcp-server

# Create and activate virtual environment
uv venv
source .venv/bin/activate

# Install with test dependencies
uv pip install -e ".[test]"
```

### Running the Server

The server supports multiple transport protocols:

```bash
# STDIO (default) - for local tools and command-line scripts
python -m src.arxiv_mcp_server.server

# HTTP - for web deployments
python -m src.arxiv_mcp_server.server --transport http --host 0.0.0.0 --port 8000

# SSE - for compatibility with existing SSE clients
python -m src.arxiv_mcp_server.server --transport sse --host 0.0.0.0 --port 8000
```

### 🔌 MCP Integration

Add this configuration to your MCP client config file:

```json
{
    "mcpServers": {
        "arxiv-mcp-server": {
            "command": "uv",
            "args": [
                "tool",
                "run",
                "arxiv-mcp-server",
                "--storage-path", "/path/to/paper/storage"
            ]
        }
    }
}
```

For Development:

```json
{
    "mcpServers": {
        "arxiv-mcp-server": {
            "command": "uv",
            "args": [
                "--directory",
                "path/to/cloned/arxiv-mcp-server",
                "run",
                "arxiv-mcp-server",
                "--storage-path", "/path/to/paper/storage"
            ]
        }
    }
}
```

## 💡 Available Tools

The server provides four main tools built with FastMCP's decorator-based approach:

### 1. Paper Search
Search for papers with optional filters:

```python
result = await call_tool("search_papers", {
    "query": "transformer architecture",
    "max_results": 10,
    "date_from": "2023-01-01",  # Optional: YYYY-MM-DD format
    "date_to": "2024-01-01",    # Optional: YYYY-MM-DD format
    "categories": ["cs.AI", "cs.LG"]  # Optional: arXiv categories
})
```

### 2. Paper Download
Download a paper by its arXiv ID:

```python
result = await call_tool("download_paper", {
    "paper_id": "2401.12345",
    "check_status": False  # Optional: check conversion status only
})
```

### 3. List Papers
View all downloaded papers:

```python
result = await call_tool("list_papers", {})
```

### 4. Read Paper
Access the content of a downloaded paper:

```python
result = await call_tool("read_paper", {
    "paper_id": "2401.12345"
})
```

## 📝 Research Prompts

The server offers specialized prompts to help analyze academic papers:

### Paper Analysis Prompt
A comprehensive workflow for analyzing academic papers that only requires a paper ID:

```python
result = await call_prompt("deep_paper_analysis", {
    "paper_id": "2401.12345",
    "expertise_level": "intermediate",  # Optional: beginner, intermediate, expert
    "analysis_focus": "general"         # Optional: general, methodology, results, etc.
})
```

This prompt includes:
- Detailed instructions for using available tools (list_papers, download_paper, read_paper, search_papers)
- A systematic workflow for paper analysis
- Comprehensive analysis structure covering:
  - Executive summary
  - Research context
  - Methodology analysis
  - Results evaluation
  - Practical and theoretical implications
  - Future research directions
  - Broader impacts

## ⚙️ Configuration

Configure through environment variables:

| Variable | Purpose | Default |
|----------|---------|---------|
| `ARXIV_STORAGE_PATH` | Paper storage location | ~/.arxiv-mcp-server/papers |

## 🧪 Testing

Run the test suite:

```bash
python -m pytest
```

### Testing with FastMCP Client

You can also test the server using FastMCP's in-memory client:

```python
from fastmcp import Client
from src.arxiv_mcp_server.server import mcp

async with Client(mcp) as client:
    # Test search functionality
    result = await client.call_tool("search_papers", {
        "query": "machine learning",
        "max_results": 3
    })
    print(result.text)
    
    # Test prompt functionality
    prompt_result = await client.get_prompt("deep_paper_analysis", {
        "paper_id": "2301.12345"
    })
    print(prompt_result.text)
```

## 📄 License

Released under the MIT License. See the LICENSE file for details.

---

<div align="center">

Made with ❤️ by the Pearl Labs Team

<a href="https://glama.ai/mcp/servers/04dtxi5i5n"><img width="380" height="200" src="https://glama.ai/mcp/servers/04dtxi5i5n/badge" alt="ArXiv Server MCP server" /></a>
</div>

## 🚀 FastMCP Migration

This server has been migrated to FastMCP v2, providing:
- **Simplified Development**: Decorator-based tool and prompt definitions
- **Type Safety**: Automatic schema generation from Python type hints
- **Better Performance**: Optimized MCP implementation
- **Multiple Transports**: Support for STDIO, HTTP, and SSE
- **Enhanced Testing**: In-memory testing capabilities

## Attributions

Thank you to arXiv for use of its open access interoperability.
