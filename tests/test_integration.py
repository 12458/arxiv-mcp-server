"""Integration tests for the complete FastMCP server."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock
from fastmcp import Client
from arxiv_mcp_server.server import mcp


@pytest.fixture
def temp_storage():
    """Create a temporary storage directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the storage path
        with patch("arxiv_mcp_server.config.Settings.STORAGE_PATH", Path(tmpdir)):
            yield Path(tmpdir)


@pytest.mark.asyncio
async def test_complete_server_functionality(temp_storage):
    """Test the complete server functionality with all tools and prompts."""
    async with Client(mcp) as client:
        # Test 1: List tools
        tools = await client.list_tools()
        tool_names = [tool.name for tool in tools]
        expected_tools = ["search_papers", "download_paper", "list_papers", "read_paper"]
        assert all(tool in tool_names for tool in expected_tools)
        
        # Test 2: List prompts
        prompts = await client.list_prompts()
        prompt_names = [prompt.name for prompt in prompts]
        assert "deep_paper_analysis" in prompt_names
        
        # Test 3: Search papers
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = AsyncMock()
            mock_response.json.return_value = [{
                "id": "2103.12345",
                "title": "Test Paper",
                "abstract": "Test abstract",
                "authors": "John Doe, Jane Smith",
                "date": "2023-01-01T00:00:00",
                "categories": ["cs.AI", "cs.LG"],
                "score": 0.85
            }]
            mock_response.raise_for_status.return_value = None
            
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            search_result = await client.call_tool("search_papers", {
                "query": "machine learning",
                "max_results": 1
            })
            
            content = json.loads(search_result.text)
            assert content["total_results"] == 1
            assert content["papers"][0]["id"] == "2103.12345"
        
        # Test 4: Download paper
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.content = b"Mock PDF Content"
            mock_response.raise_for_status.return_value = None
            
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            download_result = await client.call_tool("download_paper", {
                "paper_id": "2103.12345",
                "check_status": False
            })
            
            content = json.loads(download_result.text)
            assert "status" in content
        
        # Test 5: List papers
        with patch("arxiv.Client") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.results.return_value = []
            mock_client_class.return_value = mock_client
            
            list_result = await client.call_tool("list_papers", {})
            content = json.loads(list_result.text)
            assert "total_papers" in content
            assert "papers" in content
        
        # Test 6: Read paper
        with patch("pathlib.Path.exists") as mock_exists, \
             patch("pathlib.Path.read_text") as mock_read_text:
            
            mock_exists.return_value = True
            mock_read_text.return_value = "Mock paper content"
            
            read_result = await client.call_tool("read_paper", {
                "paper_id": "2103.12345"
            })
            
            content = json.loads(read_result.text)
            assert content["status"] == "success"
            assert content["paper_id"] == "2103.12345"
        
        # Test 7: Get prompt
        prompt_result = await client.get_prompt("deep_paper_analysis", {
            "paper_id": "2103.12345",
            "expertise_level": "intermediate",
            "analysis_focus": "general"
        })
        
        assert prompt_result.text is not None
        assert "2103.12345" in prompt_result.text


@pytest.mark.asyncio
async def test_optional_parameters():
    """Test that all optional parameters work correctly."""
    async with Client(mcp) as client:
        # Test search_papers with all optional parameters
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = AsyncMock()
            mock_response.json.return_value = []
            mock_response.raise_for_status.return_value = None
            
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            result = await client.call_tool("search_papers", {
                "query": "test query",
                "max_results": 5,
                "date_from": "2023-01-01",
                "date_to": "2024-01-01",
                "categories": ["cs.AI", "cs.LG"]
            })
            
            assert result.text is not None
        
        # Test download_paper with check_status
        result = await client.call_tool("download_paper", {
            "paper_id": "2103.12345",
            "check_status": True
        })
        
        assert result.text is not None
        
        # Test deep_paper_analysis with minimal parameters
        result = await client.get_prompt("deep_paper_analysis", {
            "paper_id": "2103.12345"
        })
        
        assert result.text is not None


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in the server."""
    async with Client(mcp) as client:
        # Test search_papers with network error
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = AsyncMock()
            mock_response.raise_for_status.side_effect = Exception("Network error")
            
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            result = await client.call_tool("search_papers", {
                "query": "test query",
                "max_results": 1
            })
            
            assert "Error" in result.text
        
        # Test read_paper with non-existent paper
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = False
            
            result = await client.call_tool("read_paper", {
                "paper_id": "nonexistent.12345"
            })
            
            content = json.loads(result.text)
            assert content["status"] == "error"


@pytest.mark.asyncio
async def test_type_validation():
    """Test that FastMCP properly validates parameter types."""
    async with Client(mcp) as client:
        # Test with invalid parameter types
        with pytest.raises(Exception):
            await client.call_tool("search_papers", {
                "query": 123,  # Should be string
                "max_results": "invalid"  # Should be int
            })
        
        with pytest.raises(Exception):
            await client.call_tool("download_paper", {
                "paper_id": 123,  # Should be string
                "check_status": "invalid"  # Should be bool
            })


@pytest.mark.asyncio
async def test_server_capabilities():
    """Test that the server exposes the correct capabilities."""
    async with Client(mcp) as client:
        # Test that tools have proper schemas
        tools = await client.list_tools()
        
        for tool in tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'inputSchema')
            
            # Verify schema structure
            schema = tool.inputSchema
            assert "type" in schema
            assert "properties" in schema
        
        # Test that prompts have proper structure
        prompts = await client.list_prompts()
        
        for prompt in prompts:
            assert hasattr(prompt, 'name')
            assert hasattr(prompt, 'description')
            assert hasattr(prompt, 'arguments')


@pytest.mark.asyncio
async def test_context_support():
    """Test that the server supports FastMCP context features."""
    # This test verifies that the server can handle context parameters
    # even though we're not using them in the current implementation
    async with Client(mcp) as client:
        # Test that tools can be called without context (ctx parameter is optional)
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = AsyncMock()
            mock_response.json.return_value = []
            mock_response.raise_for_status.return_value = None
            
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            result = await client.call_tool("search_papers", {
                "query": "test query"
            })
            
            assert result.text is not None 