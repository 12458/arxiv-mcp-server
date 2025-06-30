"""Tests for paper search functionality."""

import pytest
import json
from unittest.mock import patch, AsyncMock
import httpx
from arxiv_mcp_server.tools import handle_search


@pytest.mark.asyncio
async def test_basic_search(mock_httpx_client):
    """Test basic paper search functionality."""
    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        result = await handle_search({"query": "test query", "max_results": 1})

        assert len(result) == 1
        print(f"DEBUG: result[0] = {result[0]}")  # Debug output
        content = json.loads(result[0])
        print(f"DEBUG: content = {content}")  # Debug output
        assert content["total_results"] == 1
        paper = content["papers"][0]
        assert paper["id"] == "2103.12345"
        assert paper["title"] == "Test Paper"
        assert "resource_uri" in paper
        assert "score" in paper


@pytest.mark.asyncio
async def test_search_with_categories(mock_httpx_client):
    """Test paper search with category filtering."""
    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        result = await handle_search(
            {"query": "test query", "categories": ["cs.AI", "cs.LG"], "max_results": 1}
        )

        content = json.loads(result[0])
        assert content["papers"][0]["categories"] == ["cs.AI", "cs.LG"]


@pytest.mark.asyncio
async def test_search_with_dates(mock_httpx_client):
    """Test paper search with date filtering."""
    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        result = await handle_search(
            {
                "query": "test query",
                "date_from": "2022-01-01",
                "date_to": "2024-01-01",
                "max_results": 1,
            }
        )

        content = json.loads(result[0])
        assert content["total_results"] == 1
        assert len(content["papers"]) == 1


@pytest.mark.asyncio
async def test_search_with_invalid_dates(mock_httpx_client):
    """Test search with invalid date formats."""
    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        result = await handle_search(
            {"query": "test query", "date_from": "invalid-date", "max_results": 1}
        )

        content = json.loads(result[0])
        assert "error" in content
        assert "Invalid date format" in content["error"]


@pytest.mark.asyncio
async def test_search_semantic_query_handling(mock_httpx_client):
    """Test that semantic search handles natural language queries properly."""
    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        # Test that natural language queries are passed through unchanged
        result = await handle_search({"query": "quantum computing applications", "max_results": 1})
        
        content = json.loads(result[0])
        assert content["total_results"] == 1
        assert content["papers"][0]["score"] == 0.85
        assert content["papers"][0]["authors"] == ["John Doe", "Jane Smith"]  # Test author parsing


@pytest.mark.asyncio
async def test_search_pagination_multiple_pages(mock_httpx_client_paginated):
    """Test that pagination works correctly when requesting more results than single page."""
    with patch("httpx.AsyncClient", return_value=mock_httpx_client_paginated):
        # Request 3 results, which should trigger pagination (2 from page 1, 1 from page 2)
        result = await handle_search({"query": "test query", "max_results": 3})
        
        # Verify multiple API calls were made
        assert mock_httpx_client_paginated.call_count() == 2
        
        content = json.loads(result[0])
        assert content["total_results"] == 3
        assert len(content["papers"]) == 3
        
        # Verify papers from both pages are included
        paper_ids = [paper["id"] for paper in content["papers"]]
        assert "2103.12345" in paper_ids  # From page 1
        assert "2103.12346" in paper_ids  # From page 1  
        assert "2103.12347" in paper_ids  # From page 2


@pytest.mark.asyncio 
async def test_search_pagination_stops_on_empty_response(mock_httpx_client_paginated):
    """Test that pagination stops when API returns empty results."""
    with patch("httpx.AsyncClient", return_value=mock_httpx_client_paginated):
        # Request many results to trigger pagination until empty response
        result = await handle_search({"query": "test query", "max_results": 20})
        
        # Should have made 3 calls: page 1 (2 results), page 2 (1 result), page 3 (empty - stops)
        assert mock_httpx_client_paginated.call_count() == 3
        
        content = json.loads(result[0])
        # Should get all available results (3 total)
        assert content["total_results"] == 3
        assert len(content["papers"]) == 3


@pytest.mark.asyncio
async def test_search_pagination_with_category_filtering(mock_httpx_client_paginated):
    """Test that category filtering works correctly with pagination."""
    with patch("httpx.AsyncClient", return_value=mock_httpx_client_paginated):
        # Filter for cs.AI category only
        result = await handle_search({
            "query": "test query", 
            "categories": ["cs.AI"], 
            "max_results": 5
        })
        
        content = json.loads(result[0])
        
        # Should include papers with cs.AI category
        filtered_papers = [p for p in content["papers"] if "cs.AI" in p["categories"]]
        assert len(filtered_papers) == content["total_results"]
        
        # Verify specific papers that should match
        paper_ids = [paper["id"] for paper in content["papers"]]
        assert "2103.12345" in paper_ids  # Has cs.AI
        assert "2103.12347" in paper_ids  # Has cs.AI
        # "2103.12346" should be filtered out (only has cs.LG)


@pytest.mark.asyncio
async def test_author_string_parsing(mock_httpx_client):
    """Test that author strings are correctly parsed from comma-separated format."""
    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        result = await handle_search({"query": "test", "max_results": 2})
        
        content = json.loads(result[0])
        papers = content["papers"]
        
        # Test first paper: "John Doe, Jane Smith" -> ["John Doe", "Jane Smith"]
        assert papers[0]["authors"] == ["John Doe", "Jane Smith"]
        
        # Test second paper: "Alice Brown, Bob Wilson" -> ["Alice Brown", "Bob Wilson"]  
        assert papers[1]["authors"] == ["Alice Brown", "Bob Wilson"]


@pytest.mark.asyncio
async def test_response_format_validation(mock_httpx_client):
    """Test that response format matches expected structure."""
    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        result = await handle_search({"query": "test", "max_results": 1})
        
        content = json.loads(result[0])
        
        # Verify top-level structure
        assert "total_results" in content
        assert "papers" in content
        assert isinstance(content["papers"], list)
        
        paper = content["papers"][0]
        
        # Verify all required fields are present
        required_fields = ["id", "title", "authors", "abstract", "categories", 
                          "published", "url", "resource_uri", "score"]
        for field in required_fields:
            assert field in paper, f"Missing field: {field}"
        
        # Verify field types
        assert isinstance(paper["id"], str)
        assert isinstance(paper["title"], str)
        assert isinstance(paper["authors"], list)
        assert isinstance(paper["abstract"], str)
        assert isinstance(paper["categories"], list)
        assert isinstance(paper["published"], str)
        assert isinstance(paper["url"], str)
        assert isinstance(paper["resource_uri"], str)
        assert isinstance(paper["score"], (int, float))
        
        # Verify URL format
        assert paper["url"] == f"https://arxiv.org/pdf/{paper['id']}.pdf"
        
        # Verify resource URI format
        assert paper["resource_uri"] == f"arxiv://{paper['id']}"


@pytest.mark.asyncio
async def test_single_author_parsing():
    """Test parsing of papers with single authors."""
    # Create a mock response with single author
    single_author_response = [{
        "id": "2103.12348", 
        "journal": "arxiv",
        "title": "Single Author Paper",
        "abstract": "Test abstract",
        "authors": "Solo Author",
        "date": "2023-01-01T00:00:00",
        "categories": ["cs.AI"],
        "short_author": "S. Author",
        "score": 0.9
    }]
    
    mock_response = AsyncMock()
    mock_response.json.return_value = single_author_response
    mock_response.raise_for_status.return_value = None
    
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await handle_search({"query": "test", "max_results": 1})
        
        content = json.loads(result[0])
        paper = content["papers"][0]
        
        # Single author should still be in a list
        assert paper["authors"] == ["Solo Author"]


@pytest.mark.asyncio
async def test_http_error_handling():
    """Test handling of HTTP errors from ArxivXplorer API."""
    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.HTTPError("API error")
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await handle_search({"query": "test", "max_results": 1})
        
        content = json.loads(result[0])
        assert "error" in content
        assert "HTTP request failed" in content["error"]


@pytest.mark.asyncio
async def test_malformed_api_response():
    """Test handling of malformed API responses."""
    mock_response = AsyncMock()
    mock_response.json.return_value = {"not": "a list"}  # Invalid format
    mock_response.raise_for_status.return_value = None
    
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await handle_search({"query": "test", "max_results": 1})
        
        content = json.loads(result[0])
        assert "error" in content
        assert "Unexpected response format" in content["error"]
