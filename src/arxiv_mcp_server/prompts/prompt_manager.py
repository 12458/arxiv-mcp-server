"""Research journey prompt management for the arXiv MCP server."""

from typing import Dict, Optional, List, Any
from mcp.types import Prompt, PromptMessage, TextContent
from .prompts import PROMPTS

# Global prompt manager instance
_prompt_manager: Optional[Dict[str, Prompt]] = None

# Research session tracking for associating prompts with a user session
_research_sessions: Dict[str, Dict[str, Any]] = {}


def get_prompt_manager() -> Dict[str, Prompt]:
    """Get or create the global prompt manager dictionary.

    Returns:
        Dict[str, Prompt]: Dictionary of available prompts
    """
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PROMPTS

    return _prompt_manager


def register_prompt(prompt: Prompt) -> None:
    """Register a new prompt in the prompt manager.

    Args:
        prompt (Prompt): The prompt to register
    """
    manager = get_prompt_manager()
    manager[prompt.name] = prompt


def create_research_session(
    session_id: str, initial_metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Create a new research session to track context across prompts.

    Args:
        session_id: Unique identifier for the user session
        initial_metadata: Optional initial metadata for the session
    """
    global _research_sessions
    if session_id in _research_sessions:
        return  # Session already exists

    _research_sessions[session_id] = {
        "domain": initial_metadata.get("domain") if initial_metadata else None,
        "expertise_level": (
            initial_metadata.get("expertise_level", "intermediate")
            if initial_metadata
            else "intermediate"
        ),
        "topics": [],
        "papers": {},  # paper_id -> metadata
        "analyses": {},  # paper_id -> analysis info
        "research_questions": [],
        "prompt_history": [],  # List of prompts used in this session
    }


def get_research_session(session_id: str) -> Dict[str, Any]:
    """Get research session data for a given session ID.

    Args:
        session_id: Unique identifier for the user session

    Returns:
        Session data dictionary

    Raises:
        ValueError: If session doesn't exist
    """
    if session_id not in _research_sessions:
        raise ValueError(f"Research session not found: {session_id}")

    return _research_sessions[session_id]


def update_session_from_prompt(
    session_id: str, prompt_name: str, arguments: Dict[str, str]
) -> None:
    """Update research session with data from a prompt.

    Args:
        session_id: Unique identifier for the user session
        prompt_name: Name of the prompt being used
        arguments: Arguments provided to the prompt

    Raises:
        ValueError: If session doesn't exist
    """
    if session_id not in _research_sessions:
        create_research_session(session_id)

    session = _research_sessions[session_id]

    # Track prompt usage
    session["prompt_history"].append(
        {
            "name": prompt_name,
            "arguments": arguments,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        }
    )

    # Update research metadata based on prompt type and arguments
    if "expertise_level" in arguments:
        session["expertise_level"] = arguments["expertise_level"]

    if "domain" in arguments:
        session["domain"] = arguments["domain"]

    if prompt_name == "research-discovery" and "topic" in arguments:
        topic = arguments["topic"]
        if topic and topic not in session["topics"]:
            session["topics"].append(topic)

    elif prompt_name == "deep-paper-analysis" and "paper_id" in arguments:
        paper_id = arguments["paper_id"]
        focus = arguments.get("focus_area", "complete")

        if paper_id not in session["papers"]:
            session["papers"][paper_id] = {"id": paper_id}

        if paper_id not in session["analyses"]:
            session["analyses"][paper_id] = {"focus": focus}

    elif prompt_name == "literature-synthesis" and "paper_ids" in arguments:
        paper_ids = arguments["paper_ids"].split(",")
        for paper_id in paper_ids:
            paper_id = paper_id.strip()
            if paper_id and paper_id not in session["papers"]:
                session["papers"][paper_id] = {"id": paper_id}

    elif prompt_name == "research-question" and "topic" in arguments:
        topic = arguments["topic"]
        if topic and topic not in session["topics"]:
            session["topics"].append(topic)


def update_session_with_research_questions(
    session_id: str, questions: List[str]
) -> None:
    """Update a research session with newly generated research questions.

    Args:
        session_id: Unique identifier for the user session
        questions: List of research questions to add

    Raises:
        ValueError: If session doesn't exist
    """
    if session_id not in _research_sessions:
        raise ValueError(f"Research session not found: {session_id}")

    session = _research_sessions[session_id]

    # Add new questions, avoiding duplicates
    for question in questions:
        if question not in session["research_questions"]:
            session["research_questions"].append(question)


def suggest_next_prompts(session_id: str) -> List[Dict[str, Any]]:
    """Suggest relevant next prompts based on session context.

    Args:
        session_id: Unique identifier for the user session

    Returns:
        List of suggested prompts with prefilled arguments

    Raises:
        ValueError: If session doesn't exist
    """
    if session_id not in _research_sessions:
        raise ValueError(f"Research session not found: {session_id}")

    session = _research_sessions[session_id]
    suggestions = []

    # If user has explored topics but no papers, suggest paper analysis
    if session["topics"] and not session["papers"]:
        suggestions.append(
            {
                "prompt": "deep-paper-analysis",
                "message": "Analyze a specific paper on one of your topics of interest",
                "prefill": {
                    "domain": session["domain"],
                    "expertise_level": session["expertise_level"],
                },
            }
        )

    # If user has analyzed at least one paper, suggest literature synthesis
    if len(session["papers"]) >= 1:
        suggestions.append(
            {
                "prompt": "literature-synthesis",
                "message": "Synthesize findings across the papers you've explored",
                "prefill": {
                    "paper_ids": ",".join(session["papers"].keys()),
                    "domain": session["domain"],
                    "expertise_level": session["expertise_level"],
                },
            }
        )

    # If user has analyzed multiple papers, suggest research questions
    if len(session["papers"]) >= 2:
        suggestions.append(
            {
                "prompt": "research-question",
                "message": "Generate research questions based on your explored papers",
                "prefill": {
                    "paper_ids": ",".join(session["papers"].keys()),
                    "topic": session["topics"][-1] if session["topics"] else "",
                    "domain": session["domain"],
                    "expertise_level": session["expertise_level"],
                },
            }
        )

    # Always suggest exploring a new topic
    suggestions.append(
        {
            "prompt": "research-discovery",
            "message": "Explore a new research topic",
            "prefill": {
                "domain": session["domain"],
                "expertise_level": session["expertise_level"],
            },
        }
    )

    return suggestions
