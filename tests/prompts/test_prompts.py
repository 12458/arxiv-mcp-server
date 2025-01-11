"""Tests for the MCP prompts system."""

import pytest
from arxiv_mcp_server.prompts.prompts import PROMPTS
from arxiv_mcp_server.prompts.handlers import handle_list_prompts, handle_get_prompt, get_paper_manager

@pytest.mark.asyncio
async def test_list_prompts():
    """Test listing available prompts."""
    result = await handle_list_prompts()
    
    assert "prompts" in result
    prompts = result["prompts"]
    assert len(prompts) == len(PROMPTS)
    
    # Check each expected prompt exists
    prompt_names = {p.name for p in prompts}
    assert "research-discovery" in prompt_names
    assert "paper-analysis" in prompt_names
    assert "literature-synthesis" in prompt_names
    
    # Check prompt structure
    for prompt in prompts:
        assert prompt.name
        assert prompt.description
        assert hasattr(prompt, "arguments")

@pytest.mark.asyncio
async def test_get_prompt_research_discovery():
    """Test getting research discovery prompt."""
    arguments = {
        "topic": "machine learning",
        "expertise_level": "intermediate",
        "time_period": "2023-present"
    }
    
    result = await handle_get_prompt("research-discovery", arguments)
    
    assert "messages" in result
    messages = result["messages"]
    assert len(messages) > 0
    
    # Check first message structure
    first_msg = messages[0]
    assert first_msg.role == "user"
    assert first_msg.content.type == "text"
    assert arguments["topic"] in first_msg.content.text
    assert arguments["time_period"] in first_msg.content.text

@pytest.mark.asyncio
async def test_get_prompt_paper_analysis(mocker):
    """Test getting paper analysis prompt."""
    # Mock paper manager
    mock_content = "# Test Paper\nThis is test content"
    mocker.patch(
        'arxiv_mcp_server.resources.papers.PaperManager.get_paper_content',
        return_value=mock_content
    )
    
    arguments = {
        "paper_id": "2401.12345",
        "focus_area": "methodology"
    }
    
    result = await handle_get_prompt("paper-analysis", arguments)
    
    assert "messages" in result
    messages = result["messages"]
    assert len(messages) == 2  # Initial message + paper content
    
    # Check paper content message
    content_msg = messages[1]
    assert content_msg.role == "user"
    assert content_msg.content.type == "resource"
    assert content_msg.content.resource.uri == f"arxiv://{arguments['paper_id']}"
    assert content_msg.content.resource.text == mock_content
    assert content_msg.content.resource.mimeType == "text/markdown"

@pytest.mark.asyncio
async def test_get_prompt_paper_analysis_missing_paper(mocker):
    """Test paper analysis prompt with missing paper."""
    # Mock paper manager to return None (paper not found)
    mocker.patch(
        'arxiv_mcp_server.resources.papers.PaperManager.get_paper_content',
        return_value=None
    )
    
    arguments = {"paper_id": "2401.12345"}
    
    result = await handle_get_prompt("paper-analysis", arguments)
    
    assert "messages" in result
    messages = result["messages"]
    assert len(messages) == 2  # Initial message + download suggestion
    
    # Check download suggestion message
    suggestion_msg = messages[1]
    assert suggestion_msg.role == "assistant"
    assert suggestion_msg.content.type == "text"
    assert "download" in suggestion_msg.content.text.lower()

@pytest.mark.asyncio
async def test_get_prompt_literature_synthesis(mocker):
    """Test getting literature synthesis prompt."""
    # Mock paper manager
    mock_contents = {
        "2401.12345": "# Paper 1\nContent 1",
        "2401.67890": "# Paper 2\nContent 2"
    }
    
    async def mock_get_content(paper_id):
        return mock_contents.get(paper_id)
    
    mocker.patch(
        'arxiv_mcp_server.resources.papers.PaperManager.get_paper_content',
        side_effect=mock_get_content
    )
    
    arguments = {
        "paper_ids": ["2401.12345", "2401.67890"],
        "synthesis_type": "themes"
    }
    
    result = await handle_get_prompt("literature-synthesis", arguments)
    
    assert "messages" in result
    messages = result["messages"]
    assert len(messages) == 3  # Initial message + 2 papers
    
    # Check paper content messages
    for i, paper_id in enumerate(arguments["paper_ids"], 1):
        msg = messages[i]
        assert msg.role == "user"
        assert msg.content.type == "resource"
        assert msg.content.resource.uri == f"arxiv://{paper_id}"
        assert msg.content.resource.text == mock_contents[paper_id]
        assert msg.content.resource.mimeType == "text/markdown"

@pytest.mark.asyncio
async def test_get_prompt_invalid():
    """Test getting an invalid prompt."""
    with pytest.raises(ValueError, match="Prompt not found"):
        await handle_get_prompt("invalid-prompt", {})

@pytest.mark.asyncio
async def test_get_prompt_missing_required_args():
    """Test prompts with missing required arguments."""
    with pytest.raises(KeyError):
        await handle_get_prompt("research-discovery", {})  # Missing required 'topic'

@pytest.mark.asyncio
async def test_paper_manager_singleton():
    """Test paper manager singleton pattern."""
    manager1 = get_paper_manager()
    manager2 = get_paper_manager()
    assert manager1 is manager2  # Should be the same instance