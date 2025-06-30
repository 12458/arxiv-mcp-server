"""Search functionality for the arXiv MCP server."""

import httpx
import json
from typing import Dict, Any, List
from datetime import datetime, timezone
from dateutil import parser
from ..config import Settings

settings = Settings()


def _is_within_date_range(
    date: datetime, start: datetime | None, end: datetime | None
) -> bool:
    """Check if a date falls within the specified range."""
    if start and not start.tzinfo:
        start = start.replace(tzinfo=timezone.utc)
    if end and not end.tzinfo:
        end = end.replace(tzinfo=timezone.utc)

    if start and date < start:
        return False
    if end and date > end:
        return False
    return True


def _process_paper(paper: Dict[str, Any]) -> Dict[str, Any]:
    """Process paper information with resource URI."""
    # Parse authors string into list
    authors_str = paper.get("authors", "")
    if authors_str:
        # Handle different author formats - split by comma and clean up
        authors = [author.strip() for author in authors_str.split(",")]
    else:
        authors = []
    
    # Convert date to ISO format
    date_str = paper.get("date", "")
    if date_str:
        try:
            # Parse the date and convert to ISO format
            parsed_date = parser.parse(date_str)
            published = parsed_date.isoformat()
        except:
            published = date_str
    else:
        published = ""
    
    return {
        "id": paper.get("id", ""),
        "title": paper.get("title", ""),
        "authors": authors,
        "abstract": paper.get("abstract", ""),
        "categories": paper.get("categories", []),
        "published": published,
        "url": f"https://arxiv.org/pdf/{paper.get('id', '')}.pdf",
        "resource_uri": f"arxiv://{paper.get('id', '')}",
        "score": paper.get("score", 0.0),
    }


async def handle_search(arguments: Dict[str, Any]) -> List[str]:
    """Handle paper search requests using ArxivXplorer semantic search API.
    
    Uses pagination to fetch enough results to satisfy max_results parameter.
    Supports natural language queries for semantic search.
    """
    try:
        max_results = min(int(arguments.get("max_results", 10)), settings.MAX_RESULTS)
        query = arguments["query"]

        # Parse date filters if provided
        try:
            date_from = (
                parser.parse(arguments["date_from"]).replace(tzinfo=timezone.utc)
                if arguments.get("date_from")
                else None
            )
            date_to = (
                parser.parse(arguments["date_to"]).replace(tzinfo=timezone.utc)
                if arguments.get("date_to")
                else None
            )
        except (ValueError, TypeError) as e:
            return [f"Error: Invalid date format - {str(e)}"]

        # Make requests to ArxivXplorer API with pagination support
        all_results = []
        page = 1
        
        async with httpx.AsyncClient() as client:
            while len(all_results) < max_results:
                response = await client.get(
                    "https://search.arxivxplorer.com/",
                    params={"q": query, "page": page},
                    timeout=30.0
                )
                response.raise_for_status()
                
                raw_results = response.json()
                if not isinstance(raw_results, list):
                    return ["Error: Unexpected response format from ArxivXplorer API"]
                
                # If no results returned, we've reached the end
                if not raw_results:
                    break
                
                all_results.extend(raw_results)
                page += 1

        # Process and filter results
        results = []
        categories_filter = arguments.get("categories", [])
        
        for paper_data in all_results:
            # Apply category filtering if specified
            if categories_filter:
                paper_categories = paper_data.get("categories", [])
                if not any(cat in paper_categories for cat in categories_filter):
                    continue
            
            # Process the paper data
            processed_paper = _process_paper(paper_data)
            
            # Apply date filtering if the paper has a valid published date
            if processed_paper["published"]:
                try:
                    paper_date = parser.parse(processed_paper["published"])
                    if not paper_date.tzinfo:
                        paper_date = paper_date.replace(tzinfo=timezone.utc)
                    
                    if not _is_within_date_range(paper_date, date_from, date_to):
                        continue
                except:
                    # If date parsing fails, include the paper
                    pass
            
            results.append(processed_paper)
            
            # Limit results
            if len(results) >= max_results:
                break

        response_data = {"total_results": len(results), "papers": results}

        return [json.dumps(response_data, indent=2)]

    except httpx.HTTPError as e:
        return [f"Error: HTTP request failed - {str(e)}"]
    except Exception as e:
        return [f"Error: {str(e)}"]
