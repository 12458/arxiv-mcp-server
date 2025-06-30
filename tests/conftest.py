"""Shared test fixtures for the arXiv MCP server test suite."""

import pytest
import tempfile
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock
import arxiv
from pathlib import Path


class MockAuthor:
    def __init__(self, name):
        self.name = name


class MockLink:
    def __init__(self, href):
        self.href = href


@pytest.fixture
def mock_paper():
    """Create a properly structured mock paper with all required attributes."""
    paper = MagicMock(spec=arxiv.Result)
    paper.get_short_id.return_value = "2103.12345"
    paper.title = "Test Paper"
    paper.authors = [MockAuthor("John Doe"), MockAuthor("Jane Smith")]
    paper.summary = "Test abstract"
    paper.categories = ["cs.AI", "cs.LG"]
    paper.published = datetime(2023, 1, 1, tzinfo=timezone.utc)
    paper.pdf_url = "https://arxiv.org/pdf/2103.12345"
    paper.comment = "Test comment"
    paper.journal_ref = "Test Journal 2023"
    paper.primary_category = "cs.AI"
    paper.links = [MockLink("https://arxiv.org/abs/2103.12345")]
    return paper


@pytest.fixture
def mock_client(mock_paper):
    """Create a mock arxiv client with predefined behavior."""
    client = MagicMock(spec=arxiv.Client)
    client.results.return_value = [mock_paper]
    return client


@pytest.fixture
def temp_storage_path():
    """Create a temporary directory for paper storage during tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_pdf_content():
    """Create mock PDF content for testing."""
    return b"Mock PDF Content"


@pytest.fixture
def mock_http_response():
    """Create a mock HTTP response for testing paper downloads."""
    response = AsyncMock()
    response.status = 200
    response.__aenter__.return_value = response
    response.read.return_value = b"Mock PDF Content"
    return response


@pytest.fixture
def mock_http_session(mock_http_response):
    """Create a mock HTTP session for testing."""
    session = AsyncMock()
    session.get.return_value = mock_http_response
    session.__aenter__.return_value = session
    return session


@pytest.fixture
def mock_arxivxplorer_response():
    """Create a mock ArxivXplorer API response for testing (page 1)."""
    return [
        {
            "id": "2103.12345",
            "journal": "arxiv",
            "title": "Test Paper",
            "abstract": "Test abstract",
            "authors": "John Doe, Jane Smith",
            "date": "2023-01-01T00:00:00",
            "categories": ["cs.AI", "cs.LG"],
            "short_author": "J. Doe, et al.",
            "score": 0.85
        },
        {
            "id": "2103.12346",
            "journal": "arxiv",
            "title": "Another Test Paper",
            "abstract": "Another test abstract",
            "authors": "Alice Brown, Bob Wilson",
            "date": "2023-01-02T00:00:00",
            "categories": ["cs.LG"],
            "short_author": "A. Brown, et al.",
            "score": 0.75
        }
    ]


@pytest.fixture
def mock_arxivxplorer_response_page2():
    """Create a mock ArxivXplorer API response for testing (page 2)."""
    return [
        {
            "id": "2103.12347",
            "journal": "arxiv",
            "title": "Third Test Paper",
            "abstract": "Third test abstract",
            "authors": "Charlie Davis",
            "date": "2023-01-03T00:00:00",
            "categories": ["cs.AI"],
            "short_author": "C. Davis",
            "score": 0.65
        }
    ]


@pytest.fixture
def mock_arxivxplorer_response_empty():
    """Create an empty mock ArxivXplorer API response for testing pagination end."""
    return []


@pytest.fixture
def mock_httpx_client(mock_arxivxplorer_response):
    """Create a mock httpx client for ArxivXplorer API testing."""
    async def mock_get(*args, **kwargs):
        mock_response = AsyncMock()
        # Make json() return the actual data asynchronously
        mock_response.json = AsyncMock(return_value=mock_arxivxplorer_response)
        mock_response.raise_for_status.return_value = None
        return mock_response
    
    mock_client = AsyncMock()
    mock_client.get = mock_get
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    
    return mock_client


@pytest.fixture
def mock_httpx_client_paginated(mock_arxivxplorer_response, mock_arxivxplorer_response_page2, mock_arxivxplorer_response_empty):
    """Create a mock httpx client that supports pagination testing."""
    
    def create_client():
        call_count = 0
        
        async def get_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            # Extract page parameter from params
            params = kwargs.get('params', {})
            page = params.get('page', 1)
            
            mock_response = AsyncMock()
            mock_response.raise_for_status.return_value = None
            
            # Return different responses based on page number
            if page == 1:
                mock_response.json = AsyncMock(return_value=mock_arxivxplorer_response)
            elif page == 2:
                mock_response.json = AsyncMock(return_value=mock_arxivxplorer_response_page2)
            else:
                mock_response.json = AsyncMock(return_value=mock_arxivxplorer_response_empty)
                
            return mock_response
        
        mock_client = AsyncMock()
        mock_client.get = get_side_effect
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        
        # Add a way to check call count
        mock_client.call_count = lambda: call_count
        
        return mock_client
    
    return create_client()
