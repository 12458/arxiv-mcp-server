"""Integration tests for MCP prompts system."""

import pytest
from arxiv_mcp_server.server import server
from mcp.server.models import InitializationOptions
from arxiv_mcp_server.prompts.handlers import handle_list_prompts, handle_get_prompt

@pytest.mark.asyncio
async def test_server_prompt_capabilities():
    """Test that server correctly advertises prompt capabilities."""
    capabilities = server.get_capabilities(experimental_capabilities={})
    assert capabilities is not None
    server.capabilities = capabilities
    assert server.capabilities.get("prompts") is not None

@pytest.mark.asyncio
async def test_prompt_list_endpoint():
    """Test the prompts/list endpoint."""
    response = await handle_list_prompts()
    assert "prompts" in response
    assert len(response["prompts"]) > 0

@pytest.mark.asyncio
async def test_prompt_get_endpoint():
    """Test the prompts/get endpoint."""
    # Test research discovery prompt
    response = await handle_get_prompt("research-discovery", {"topic": "machine learning"})
    assert "messages" in response
    assert len(response["messages"]) > 0

@pytest.mark.asyncio
async def test_prompt_error_handling():
    """Test error handling in prompt endpoints."""
    # Test invalid prompt name
    with pytest.raises(ValueError, match="Prompt not found"):
        await handle_get_prompt("invalid-prompt", {})
    
    # Test missing required argument
    with pytest.raises(KeyError):
        await handle_get_prompt("research-discovery", {})

@pytest.mark.asyncio
async def test_prompt_with_paper_resources(mocker):
    """Test prompts that use paper resources."""
    # Mock paper manager
    mock_content = "# Test Paper\nThis is test content"
    mocker.patch(
        'arxiv_mcp_server.resources.papers.PaperManager.get_paper_content',
        return_value=mock_content
    )
    
    response = await handle_get_prompt("paper-analysis", {"paper_id": "2401.12345"})
    messages = response["messages"]
    
    # Check that paper content is included
    resource_messages = [m for m in messages if m.content.type == "resource"]
    assert len(resource_messages) == 1
    assert resource_messages[0].content.resource.text == mock_content