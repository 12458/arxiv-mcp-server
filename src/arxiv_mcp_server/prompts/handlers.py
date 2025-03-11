"""Handlers for prompt-related requests with paper analysis functionality."""

from typing import List, Dict, Optional
from mcp.types import Prompt, PromptMessage, TextContent, GetPromptResult
from .prompts import PROMPTS
from .deep_research_analysis_prompt import PAPER_ANALYSIS_PROMPT
from .prompt_manager import (
    get_research_session,
    create_research_session,
    update_session_from_prompt,
)


# Legacy global research context - used as fallback when no session_id is provided
class ResearchContext:
    """Maintains context throughout a research session."""

    def __init__(self):
        self.expertise_level = "intermediate"  # default
        self.explored_papers = {}  # paper_id -> basic metadata
        self.paper_analyses = {}  # paper_id -> analysis focus and summary

    def update_from_arguments(self, args: Dict[str, str]) -> None:
        """Update context based on new arguments."""
        if "expertise_level" in args:
            self.expertise_level = args["expertise_level"]
        if "paper_id" in args and args["paper_id"] not in self.explored_papers:
            self.explored_papers[args["paper_id"]] = {"id": args["paper_id"]}


# Global research context for backward compatibility
_research_context = ResearchContext()

# Citation and evidence standards by domain
CITATION_STANDARDS = {
    "computer_science": "Include specific section numbers and algorithm references",
    "physics": "Reference equations and experimental results by number",
    "biology": "Include methodology details and statistical significance",
    "default": "Reference specific findings and methodologies from the papers",
}

# Output structure for deep paper analysis
OUTPUT_STRUCTURE = """
Present your analysis with the following structure:
1. Executive Summary: 3-5 sentence overview of key contributions
2. Detailed Analysis: Following the specific focus requested
3. Visual Breakdown: Describe key figures/tables and their significance
4. Related Work Map: Position this paper within the research landscape
5. Implementation Notes: Practical considerations for applying these findings
"""


async def list_prompts() -> List[Prompt]:
    """Handle prompts/list request."""
    # Filter to only include deep-paper-analysis
    return [PROMPTS["deep-paper-analysis"]] if "deep-paper-analysis" in PROMPTS else []


async def get_prompt(
    name: str, arguments: Dict[str, str] | None = None, session_id: Optional[str] = None
) -> GetPromptResult:
    """Handle prompts/get request for paper analysis.

    Args:
        name: The name of the prompt to get
        arguments: The arguments to use with the prompt
        session_id: Optional user session ID for context persistence

    Returns:
        GetPromptResult: The resulting prompt with messages

    Raises:
        ValueError: If prompt not found or arguments invalid
    """
    if name != "deep-paper-analysis":
        raise ValueError(f"Prompt not found: {name}")

    prompt = PROMPTS[name]
    if arguments is None:
        raise ValueError(f"No arguments provided for prompt: {name}")

    # Validate required arguments
    for arg in prompt.arguments:
        if arg.required and (arg.name not in arguments or not arguments.get(arg.name)):
            raise ValueError(f"Missing required argument: {arg.name}")

    # Get research context - either from session or fallback to global
    context = None
    if session_id:
        try:
            # Try to get existing session
            session_data = get_research_session(session_id)
            context = session_data
        except ValueError:
            # Create new session if it doesn't exist
            create_research_session(session_id, arguments)
            context = get_research_session(session_id)

        # Update session with current prompt info
        update_session_from_prompt(session_id, name, arguments)
    else:
        # Fallback to global context for backward compatibility
        _research_context.update_from_arguments(arguments)
        context = _research_context

    # Determine domain-specific guidance
    domain = "default"  # Default domain since it's no longer required
    citation_guidance = CITATION_STANDARDS.get(domain, CITATION_STANDARDS["default"])

    # Process deep-paper-analysis prompt
    paper_id = arguments.get("paper_id", "")

    # Add context from previous papers if available
    previous_papers_context = ""

    if session_id:
        # Get papers from session
        papers = context.get("papers", {})
        if len(papers) > 1:
            previous_ids = [pid for pid in papers.keys() if pid != paper_id]
            if previous_ids:
                previous_papers_context = f"\nI've previously analyzed papers: {', '.join(previous_ids)}. If relevant, note connections to these works."
    else:
        # Use global context
        if len(_research_context.explored_papers) > 1:
            previous_ids = [
                pid
                for pid in _research_context.explored_papers.keys()
                if pid != paper_id
            ]
            if previous_ids:
                previous_papers_context = f"\nI've previously analyzed papers: {', '.join(previous_ids)}. If relevant, note connections to these works."

    # Track this analysis in context (for global context only, session is updated above)
    if not session_id:
        _research_context.paper_analyses[paper_id] = {"analysis": "complete"}

    return GetPromptResult(
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"Analyze paper {paper_id}.{previous_papers_context}\n\n"
                    f"{citation_guidance}\n\n{OUTPUT_STRUCTURE}\n\n{PAPER_ANALYSIS_PROMPT}",
                ),
            )
        ]
    )
