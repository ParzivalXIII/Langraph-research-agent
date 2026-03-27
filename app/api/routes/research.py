"""Research API routes for processing research queries.

Provides REST endpoints for submitting research queries and retrieving
research briefs with source traceability and contradiction analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.agents.research_agent import ResearchAgent
from app.core.database import get_db
from app.core.errors import AppError
from app.core.logging import get_logger
from app.schemas.research import ResearchBrief, ResearchQuery

logger = get_logger(__name__)

router = APIRouter(prefix="/research", tags=["research"])

# Initialize agent
_research_agent = ResearchAgent()


@router.post(
    "/",
    response_model=ResearchBrief,
    status_code=status.HTTP_200_OK,
    summary="Get a research brief",
    description="Submit a research query and receive a synthesized research brief with sources, contradictions, and confidence score.",
)
async def post_research(
    query: ResearchQuery,
    session: Session = Depends(get_db),
) -> ResearchBrief:
    """Process a research query and return a structured brief.

    Orchestrates the bounded research agent to:
    1. Validate input query
    2. Retrieve sources via Tavily API
    3. Detect contradictions between sources
    4. Synthesize findings with confidence score
    5. Return structured research brief

    Args:
        query: Research query (depth, max_sources, time_range, query string)
        session: Database session for optional persistence (Phase 4+)

    Returns:
        ResearchBrief with summary, key_points, sources, contradictions, confidence_score

    Raises:
        HTTPException 400: Invalid query input (validation error)
        HTTPException 503: External service failure (Tavily, etc.)
    """
    logger.info(
        "research_request_received",
        query=query.query[:100],
        depth=query.depth,
        max_sources=query.max_sources,
        time_range=query.time_range,
    )

    try:
        # Process query through research agent
        brief = await _research_agent.process_query(query)

        logger.info(
            "research_request_complete",
            query=query.query[:100],
            sources_count=len(brief.sources),
            confidence_score=brief.confidence_score,
        )

        return brief

    except AppError as exc:
        logger.error(
            "research_request_app_error",
            query=query.query[:100],
            error_code=exc.error_code,
            error_message=exc.message,
        )

        # Map error codes to HTTP status codes
        if exc.error_code == "VALIDATION_ERROR":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=exc.message,
            ) from exc
        elif exc.error_code == "NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=exc.message,
            ) from exc
        elif "ERROR" in exc.error_code and (
            "RATE_LIMIT" in exc.error_code
            or "429" in str(exc.details.get("status_code", ""))
        ):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"{exc.error_code}: {exc.message}",
            ) from exc
        elif "ERROR" in exc.error_code:  # Catch *_ERROR codes as service errors
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"{exc.error_code}: {exc.message}",
            ) from exc
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during research processing",
            ) from exc

    except Exception as exc:
        logger.error(
            "research_request_unexpected_error",
            query=query.query[:100],
            error=str(exc),
            error_type=type(exc).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error during research processing",
        ) from exc
