"""
Full research query diagnostic script.

This script runs a complete research query with intermediate depth and logs all API calls made by the research agent. It is designed to help diagnose issues in the full query flow, including:
- LLM interactions (summary and key points generation)
- Tavily search calls
- Any other API calls made during the process

Run with:
    uv run diagnose_full_query.py "your research question"

Or with a specific depth:
    uv run diagnose_full_query.py "question" intermediate
"""

import asyncio
import logging
import sys
from app.agents.research_agent import ResearchAgent
from app.core.logging import configure_logging
from app.schemas.research import ResearchQuery
from app.core.config import get_settings

# Setup logging to show DEBUG level (where API calls are logged)
settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

async def main():
    """Run a full research query and log all API calls."""
    
    # Get query from CLI or use default
    if len(sys.argv) > 1:
        query_text = sys.argv[1]
    else:
        query_text = "What are the latest developments in quantum computing in 2024?"
    
    # Get depth from CLI or use default
    depth = sys.argv[2] if len(sys.argv) > 2 else "intermediate"
    
    print(f"\n{'='*70}")
    print("🔍 FULL RESEARCH QUERY DIAGNOSTIC")
    print(f"{'='*70}")
    print(f"Query: {query_text}")
    print(f"Depth: {depth}")
    print("\nMonitoring for 'llm_api_call_made' events in the logs below:")
    print(f"{'='*70}\n")
    
    # Create the research agent
    agent = ResearchAgent()
    
    # Create research query
    research_query = ResearchQuery(
        query=query_text,
        depth=depth,
    )
    
    # Run the research query
    try:
        brief = await agent.process_query(research_query)
        
        print(f"\n{'='*70}")
        print("✅ RESEARCH COMPLETE")
        print(f"{'='*70}\n")
        
        # Display the result
        print("RESEARCH BRIEF:")
        print("-" * 70)
        print(f"Summary:\n{brief.summary}\n")
        print("Key Points:")
        for i, point in enumerate(brief.key_points, 1):
            print(f"  {i}. {point}")
        print(f"\nSources: {len(brief.sources)}")
        print(f"Confidence Score: {brief.confidence_score}")
        print("-" * 70)
        
        print("\n📊 NEXT STEPS:")
        print("1. Count the number of 'llm_api_call_made' log entries above")
        print("2. Expected: ~2 calls (summary + key_points)")
        print("3. Actual: Check logs for exact count")
        print("4. Look at session_id correlation to see which method made each call")
        print("\nTo count API calls:")
        print("  grep 'llm_api_call_made' <output_file> | wc -l")
        
    except Exception as e:
        print(f"\n❌ ERROR during research: {e}")
        logger.exception("Research query failed")
        raise

if __name__ == "__main__":
    asyncio.run(main())
