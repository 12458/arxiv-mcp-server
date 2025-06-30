"""Read functionality for the arXiv MCP server."""

import json
from pathlib import Path
from typing import Dict, Any, List
from ..config import Settings

settings = Settings()


def list_papers() -> list[str]:
    """List all stored paper IDs."""
    return [p.stem for p in Path(settings.STORAGE_PATH).glob("*.md")]


async def handle_read_paper(arguments: Dict[str, Any]) -> List[str]:
    """Handle requests to read a paper's content."""
    try:
        paper_ids = list_papers()
        paper_id = arguments["paper_id"]
        # Check if paper exists
        if paper_id not in paper_ids:
            return [
                json.dumps(
                    {
                        "status": "error",
                        "message": f"Paper {paper_id} not found in storage. You may need to download it first using download_paper.",
                    }
                )
            ]

        # Get paper content
        content = Path(settings.STORAGE_PATH, f"{paper_id}.md").read_text(
            encoding="utf-8"
        )

        return [
            json.dumps(
                {
                    "status": "success",
                    "paper_id": paper_id,
                    "content": content,
                }
            )
        ]

    except Exception as e:
        return [
            json.dumps(
                {
                    "status": "error",
                    "message": f"Error reading paper: {str(e)}",
                }
            )
        ]
