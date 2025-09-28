"""
Synchronous runner for link analysis to be used from the orchestrator.
"""
import asyncio
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def run_link_analysis_sync(urls: List[str], mcp_session) -> Dict[str, Any]:
    """
    Run link analysis synchronously by creating a new event loop.
    
    Args:
        urls: List of URLs to analyze
        mcp_session: The MCP Playwright session
        
    Returns:
        Dict containing the link analysis report
    """
    logger.info(f"🔗 Starting synchronous link analysis for {len(urls)} URLs")
    
    # Create a new event loop for the async operations
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Run the async link analysis
        result = loop.run_until_complete(_run_link_analysis_async(urls, mcp_session))
        logger.info("✅ Link analysis completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"❌ Link analysis failed: {str(e)}")
        raise
        
    finally:
        # Clean up the event loop
        loop.close()


async def _run_link_analysis_async(urls: List[str], mcp_session) -> Dict[str, Any]:
    """
    Internal async function that runs the actual link analysis.
    """
    from .graph import create_link_analysis_agent
    
    # Create the link analysis agent
    agent = create_link_analysis_agent()
    
    # Create the initial state
    initial_state = {
        "urls_to_investigate": urls,
        "investigation_transcript": [],
        "final_report": {},
        "mcp_playwright_session": mcp_session
    }
    
    # Run the analysis
    final_state = await agent.ainvoke(initial_state)
    
    # Return the final report
    return final_state.get("final_report", {})
