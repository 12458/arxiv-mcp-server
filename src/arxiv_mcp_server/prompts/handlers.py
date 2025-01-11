"""Handlers for prompt-related requests."""

import logging
from typing import Dict, Any, List
from mcp.types import (
    Prompt,
    PromptMessage,
    TextContent,
    EmbeddedResource,
    TextResourceContents,
)
from .prompts import PROMPTS
from ..resources import PaperManager

logger = logging.getLogger(__name__)

# Initialize paper manager singleton
paper_manager = None

def get_paper_manager() -> PaperManager:
    """Get or create paper manager instance."""
    global paper_manager
    if paper_manager is None:
        paper_manager = PaperManager()
    return paper_manager

async def handle_list_prompts() -> Dict[str, List[Prompt]]:
    """Handle prompts/list request."""
    return {"prompts": list(PROMPTS.values())}

async def handle_get_prompt(name: str, arguments: Dict[str, Any]) -> Dict[str, List[PromptMessage]]:
    """Handle prompts/get request."""
    prompt = PROMPTS.get(name)
    if not prompt:
        raise ValueError(f"Prompt not found: {name}")

    # Validate required arguments
    for arg in prompt.arguments or []:
        if arg.required and arg.name not in arguments:
            raise KeyError(f"Missing required argument: {arg.name}")

    messages = []
    
    # Format basic prompt message
    if name == "research-discovery":
        expertise = arguments.get("expertise_level", "intermediate")
        time_period = arguments.get("time_period", "")
        
        guide = {
            "beginner": "I'll explain key concepts and methodologies.",
            "intermediate": "We'll focus on recent developments.",
            "expert": "We'll dive deep into technical details."
        }.get(expertise, "We'll focus on recent developments.")
        
        messages.append(PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=f"""I'll help you explore research papers on {arguments['topic']}.
                {f'Time period: {time_period}' if time_period else ''}
                {guide}
                
                What specific aspects interest you most?"""
            )
        ))

    elif name == "paper-analysis":
        paper_id = arguments['paper_id']
        focus = arguments.get("focus_area", "complete")
        
        messages.append(PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=f"Let's analyze paper {paper_id} with focus on {focus}."
            )
        ))
        
        # Add paper content if available
        try:
            content = await get_paper_manager().get_paper_content(paper_id)
            if content:
                messages.append(PromptMessage(
                    role="user",
                    content=EmbeddedResource(
                        type="resource",
                        resource=TextResourceContents(
                            uri=f"arxiv://{paper_id}",
                            text=content,
                            mimeType="text/markdown"
                        )
                    )
                ))
            else:
                messages.append(PromptMessage(
                    role="assistant",
                    content=TextContent(
                        type="text",
                        text=f"I'll need to download this paper first."
                    )
                ))
        except Exception as e:
            logger.error(f"Error accessing paper {paper_id}: {str(e)}")
            messages.append(PromptMessage(
                role="assistant",
                content=TextContent(
                    type="text",
                    text=f"There was an issue accessing the paper: {str(e)}"
                )
            ))

    elif name == "literature-synthesis":
        synthesis_type = arguments.get("synthesis_type", "comprehensive")
        paper_ids = arguments["paper_ids"]
        
        messages.append(PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=f"Let's synthesize findings from: {', '.join(paper_ids)}"
            )
        ))
        
        # Add paper contents
        for paper_id in paper_ids:
            try:
                content = await get_paper_manager().get_paper_content(paper_id)
                if content:
                    messages.append(PromptMessage(
                        role="user",
                        content=EmbeddedResource(
                            type="resource",
                            resource=TextResourceContents(
                                uri=f"arxiv://{paper_id}",
                                text=content,
                                mimeType="text/markdown"
                            )
                        )
                    ))
                else:
                    messages.append(PromptMessage(
                        role="assistant",
                        content=TextContent(
                            type="text",
                            text=f"Need to download paper {paper_id} first."
                        )
                    ))
            except Exception as e:
                logger.error(f"Error accessing paper {paper_id}: {str(e)}")
                messages.append(PromptMessage(
                    role="assistant",
                    content=TextContent(
                        type="text",
                        text=f"Error accessing paper {paper_id}: {str(e)}"
                    )
                ))

    return {"messages": messages}