"""Diagnostic script to track LLM API calls.

Run this to see exactly how many API calls are made for a single LLM invocation.

Usage:
    uv run diagnose_llm_calls.py
"""

import asyncio
from app.core.logging import get_logger
from app.core.llm import get_llm_client, _llm_call_session_id

logger = get_logger(__name__)


async def main():
    """Make a single LLM call and log all requests."""
    logger.warning(f"=== Starting LLM Diagnostic Test ===")
    logger.warning(f"Session ID: {_llm_call_session_id}")
    logger.warning(f"Starting diagnostic test with a simple prompt...")

    try:
        llm = get_llm_client()
        logger.warning("LLM client obtained (or cached)")

        prompt = """You are a helpful assistant. Answer the following question briefly in 1-2 sentences.

Question: What is 2 + 2?

Answer:"""

        logger.warning(f"About to call ainvoke with prompt length: {len(prompt)}")
        response = await llm.ainvoke(prompt)
        logger.warning(
            f"Response received: {response.content if hasattr(response, 'content') else str(response)[:100]}"
        )

        logger.warning("=== Diagnostic Test Complete ===")

    except Exception as e:
        logger.error(f"Error during diagnostic: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
