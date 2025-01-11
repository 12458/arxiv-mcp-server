"""Tests for paper storage functionality."""

import pytest
import aiofiles
from unittest.mock import patch
from arxiv_mcp_server.resources import PaperStorage
from arxiv_mcp_server.config import Settings
from pathlib import Path

settings = Settings()


@pytest.mark.asyncio
async def test_store_paper(temp_storage_path, mock_pdf_content, mock_http_session):
    """Test storing a paper."""
    storage = PaperStorage(str(temp_storage_path))

    with patch("aiohttp.ClientSession", return_value=mock_http_session):
        success = await storage.store_paper(
            "2103.12345", "https://arxiv.org/pdf/2103.12345"
        )
        assert success

        paper_path = temp_storage_path / "2103.12345.pdf"
        assert paper_path.exists()

        async with aiofiles.open(paper_path, "rb") as f:
            content = await f.read()
            assert content == mock_pdf_content


@pytest.mark.asyncio
async def test_get_paper_content(temp_storage_path, mock_pdf_content):
    """Test retrieving stored paper content."""
    storage = PaperStorage()
    paper_path = Path(settings.STORAGE_PATH) / "2103.12345.pdf"

    async with aiofiles.open(paper_path, "wb") as f:
        await f.write(mock_pdf_content)

    content = await storage.get_paper_content("2103.12345")
    assert content == mock_pdf_content


@pytest.mark.asyncio
async def test_has_paper(temp_storage_path, mock_pdf_content):
    """Test checking paper availability."""
    storage = PaperStorage(str(temp_storage_path))
    paper_path = temp_storage_path / "2103.12345.pdf"

    assert not await storage.has_paper("2103.12345")

    async with aiofiles.open(paper_path, "wb") as f:
        await f.write(mock_pdf_content)

    assert await storage.has_paper("2103.12345")


@pytest.mark.asyncio
async def test_list_papers(temp_storage_path, mock_pdf_content):
    """Test listing stored papers."""
    storage = PaperStorage(str(temp_storage_path))

    # Create some test papers
    papers = ["2103.12345", "2103.67890"]
    for paper_id in papers:
        paper_path = temp_storage_path / f"{paper_id}.pdf"
        async with aiofiles.open(paper_path, "wb") as f:
            await f.write(mock_pdf_content)

    stored_papers = await storage.list_papers()
    assert set(stored_papers) == set(papers)
