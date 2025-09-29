import os
import json
import asyncio
import logging
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from typing import Literal
from pdf_hunter.agents.image_analysis.schemas import URLMissionStatus
from .tools import domain_whois
from pdf_hunter.shared.utils.serializer import dump_state_to_file
from langgraph.constants import Send
from langgraph.graph import END
from pdf_hunter.shared.utils.logging_config import get_logger


from pdf_hunter.config import url_investigation_investigator_llm, url_investigation_analyst_llm
from .schemas import URLInvestigationState, URLInvestigatorState, URLAnalysisResult, AnalystFindings
from .prompts import URL_INVESTIGATION_INVESTIGATOR_SYSTEM_PROMPT, URL_INVESTIGATION_ANALYST_SYSTEM_PROMPT, URL_INVESTIGATION_ANALYST_USER_PROMPT

# Initialize logger
logger = get_logger(__name__)



async def investigate_url(state: URLInvestigatorState):
    """Analyze current state and decide on tool usage with MCP integration.

    This node uses an LLM to determine the next steps in the investigation,
    including whether to call a tool or proceed with analysis. It integrates
    with MCP for dynamic tool execution.
    """

    url_task = state["url_task"]
    session_output_dir = state["output_directory"]
    
    logger.info(f"Starting URL investigation for: {url_task.url}")
    logger.debug(f"URL priority: {url_task.priority}, source context: {getattr(url_task, 'source_context', 'None')}")

    # Generate unique task ID for this investigation to ensure session isolation
    task_id = f"url_{abs(hash(url_task.url))}"
    logger.debug(f"Generated task ID: {task_id}")

    # Create task-specific investigation directory under url investigation
    url_investigation_dir = os.path.join(session_output_dir, "url_investigation", "investigations")
    task_investigation_dir = os.path.join(url_investigation_dir, task_id)
    os.makedirs(task_investigation_dir, exist_ok=True)
    logger.debug(f"Created investigation directory: {task_investigation_dir}")

    # Get the task-specific MCP session and load tools fresh each time
    from ...shared.utils.mcp_client import get_mcp_session
    from langchain_mcp_adapters.tools import load_mcp_tools
    
    logger.debug(f"Getting MCP session for task: {task_id}")
    session = await get_mcp_session(task_id, session_output_dir)
    logger.debug("Loading MCP tools")
    mcp_tools = await load_mcp_tools(session)
    all_tools = mcp_tools + [domain_whois]
    logger.debug(f"Loaded {len(all_tools)} tools for investigation")
    model_with_tools = url_investigation_investigator_llm.bind_tools(all_tools)

    messages = state.get("investigation_logs", [])
    if not messages:
        logger.info("Starting new URL investigation chain")
        # Get absolute path for the task investigation directory
        abs_task_investigation_dir = await asyncio.to_thread(os.path.abspath, task_investigation_dir)
        # Build context information
        source_context = getattr(url_task, 'source_context', 'PDF document')
        extraction_method = getattr(url_task, 'extraction_method', 'unknown method')
        
        initial_prompt = f"""
        Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        Begin your investigation.
        
        **INVESTIGATION BRIEFING:**
        **URL to Investigate:** {url_task.url}
        **Source Document:** {source_context}
        **Extraction Method:** {extraction_method} (from PDF page {url_task.page_number})
        **Reason Flagged:** {url_task.reason}
        **Note**: Screenshots and traces will be automatically saved to the MCP output directory for this investigation.
        
        **IMPORTANT:** This URL was extracted from a PDF document, not discovered on a website. The PDF may have used social engineering tactics (like fake verification prompts) to trick users into visiting this URL. Your investigation should focus on where this URL leads and whether it's part of a larger attack chain.
        """
        initial_messages = [ SystemMessage(content=URL_INVESTIGATION_INVESTIGATOR_SYSTEM_PROMPT), HumanMessage(content=initial_prompt) ]
        logger.debug("Created initial investigation prompt")
        
        # Get the LLM response asynchronously - proper async pattern
        logger.debug("Invoking investigator LLM")
        llm_response = await model_with_tools.ainvoke(initial_messages)
        logger.debug("Received LLM response for initial investigation")
        
        # Return both the initial messages AND the LLM response
        return {"investigation_logs": initial_messages + [llm_response]}
    else:
        # For subsequent calls, use existing messages and add only the new response
        logger.debug(f"Continuing investigation chain, turn {len(messages) // 2}")
        llm_response = await model_with_tools.ainvoke(messages)
        logger.debug("Received LLM response for continued investigation")
        return {"investigation_logs": [llm_response]}



async def execute_browser_tools(state: URLInvestigatorState):
    """Execute tool calls using browser automation through MCP."""
    
    # Safety check to handle potential issues with tool_calls format
    last_message = state["investigation_logs"][-1]
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        logger.warning("No tool calls found in the last message")
        return {"investigation_logs": state["investigation_logs"] + [ToolMessage(content="No tool calls were found to execute.", tool_call_id="none")]}
    
    tool_calls = last_message.tool_calls
    url_task = state["url_task"]
    session_output_dir = state["output_directory"]
    
    logger.info(f"Executing browser tool calls for URL: {url_task.url}")
    logger.debug(f"Found {len(tool_calls)} tool call(s) to execute")

    # Generate the same task ID as used in investigate_url for session consistency
    task_id = f"url_{abs(hash(url_task.url))}"

    # Create task-specific investigation directory under url investigation
    url_investigation_dir = os.path.join(session_output_dir, "url_investigation", "investigations")
    task_investigation_dir = os.path.join(url_investigation_dir, task_id)
    os.makedirs(task_investigation_dir, exist_ok=True)

    async def execute_tools():
        from langchain_core.tools.base import ToolException
        
        # Get the task-specific MCP session and load tools fresh each time
        from ...shared.utils.mcp_client import get_mcp_session
        from langchain_mcp_adapters.tools import load_mcp_tools
        
        logger.debug(f"Getting MCP session for tool execution: {task_id}")
        session = await get_mcp_session(task_id, session_output_dir)
        logger.debug("Loading MCP tools for execution")
        mcp_tools = await load_mcp_tools(session)
        tools = mcp_tools + [domain_whois]
        logger.debug(f"Loaded {len(tools)} tools for execution")
        tool_by_name = {tool.name: tool for tool in tools}

        # Execute tool calls (sequentially for reliability)
        observations = []
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            logger.info(f"Executing tool: {tool_name}")
            
            try:
                tool = tool_by_name[tool_name]
                
                if tool_name == "domain_whois":
                    # Use async invoke to prevent blocking
                    logger.debug(f"Running domain_whois with args: {tool_call['args']}")
                    observation = await asyncio.to_thread(tool.invoke, tool_call["args"])
                else:
                    logger.debug(f"Running MCP tool {tool_name} with args: {tool_call['args']}")
                    observation = await tool.ainvoke(tool_call["args"])
                    
                logger.debug(f"Tool {tool_name} executed successfully")
                observations.append(observation)
                
            except ToolException as e:
                # Handle tool exceptions gracefully (e.g., network errors, invalid URLs)
                error_msg = f"Tool execution failed: {str(e)}"
                logger.warning(f"Tool {tool_name} execution failed: {str(e)}")
                observations.append(error_msg)
                
            except Exception as e:
                # Handle any other unexpected errors
                error_msg = f"Unexpected error in tool '{tool_name}': {str(e)}"
                logger.error(f"Unexpected error in tool {tool_name}: {str(e)}", exc_info=True)
                observations.append(error_msg)

        tool_outputs = [
            ToolMessage(
                content=observation,
                name=tool_call["name"],
                tool_call_id=tool_call["id"]
            )
            for observation, tool_call in zip(observations, tool_calls)
        ]
        
        logger.debug(f"Created {len(tool_outputs)} tool messages")
        return tool_outputs
    
    logger.debug("Executing all tools")
    messages = await execute_tools()
    logger.info(f"Completed execution of {len(messages)} tools")

    # Return the messages to be added to the investigation_logs
    # Since add_messages handles sequences, we can return the list
    return {"investigation_logs": messages}



# --- Node 2: Analyst ---
async def analyze_url_content(state: URLInvestigatorState) -> dict:
    """Synthesizes all evidence and assembles the final report."""
    url_task = state["url_task"]
    investigation_log = state["investigation_logs"]

    logger.info(f"Starting analysis synthesis for URL: {url_task.url}")
    logger.debug(f"Investigation log contains {len(investigation_log)} messages")

    analyst_llm = url_investigation_analyst_llm.with_structured_output(AnalystFindings)
    
    logger.debug("Creating analyst prompt")
    analyst_prompt = URL_INVESTIGATION_ANALYST_USER_PROMPT.format(
        current_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        initial_briefing_json=url_task.model_dump_json(indent=2),
        investigation_log_json=json.dumps([msg.model_dump() for msg in investigation_log], indent=2)
    )
    
    logger.debug("Invoking analyst LLM for findings synthesis")
    analyst_findings = await analyst_llm.ainvoke([
        SystemMessage(content=URL_INVESTIGATION_ANALYST_SYSTEM_PROMPT),
        HumanMessage(content=analyst_prompt)
    ])

    new_status = URLMissionStatus.COMPLETED if analyst_findings.mission_status == "completed" else URLMissionStatus.FAILED
    url_task.mission_status = new_status
    logger.info(f"URL investigation complete with status: {new_status}")
    logger.debug(f"Verdict: {analyst_findings.verdict}, confidence: {analyst_findings.confidence}")

    link_analysis_final_report = URLAnalysisResult(
        initial_url=url_task,
        full_investigation_log=[msg.model_dump() for msg in investigation_log],
        analyst_findings=analyst_findings
    )
    
    logger.info(f"URL analysis summary: {analyst_findings.summary[:100]}...")
    logger.debug("Generated final URL analysis report")
    return {"link_analysis_final_report": link_analysis_final_report}


def should_continue(state: URLInvestigatorState) -> Literal["execute_browser_tools", "analyze_url_content"]:
    """Determine whether to continue with tool execution or proceed to analysis.
    This function checks the latest messages in the investigation log to see if
    any tools were called. If tools were called, it returns "execute_browser_tools" to continue
    executing tools. If no tools were called, it returns "analyze_url_content" to proceed
    to the analysis phase.
    """
    messages = state["investigation_logs"]
    last_message = messages[-1]
    
    url = state["url_task"].url
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.debug(f"URL {url}: Tool calls found, continuing with tool execution")
        return "execute_browser_tools"
    
    logger.info(f"URL {url}: No more tool calls, proceeding to analysis")
    return "analyze_url_content"


def route_url_analysis(state: URLInvestigationState):
    """
    Dispatch the link analysis tasks based on high priority URLs from visual analysis.
    Uses Send to parallelize URL analysis across multiple instances.
    """
    high_priority_urls = state.get("high_priority_urls", [])
    
    if high_priority_urls:
        logger.info(f"Found {len(high_priority_urls)} high priority URLs to analyze")
        
        for url in high_priority_urls:
            logger.debug(f"Preparing to analyze URL: {url.url} (priority: {url.priority})")
            
        return [Send("conduct_link_analysis", {
            "url_task": url,
            "output_directory": state["output_directory"]
        }) for url in high_priority_urls]
    
    logger.info("No high priority URLs found for analysis")
    return "save_url_analysis_state"


def filter_high_priority_urls(state: URLInvestigationState):
    """
    Filter and return only high priority URLs from the visual analysis report.
    """
    logger.info("Filtering high priority URLs from visual analysis report")
    
    # Create url investigation investigations directory
    session_output_dir = state.get("output_directory")
    high_priority_urls = []
    
    if session_output_dir:
        url_investigation_dir = os.path.join(session_output_dir, "url_investigation", "investigations")
        os.makedirs(url_investigation_dir, exist_ok=True)
        logger.debug(f"Created URL investigation directory: {url_investigation_dir}")

    if "visual_analysis_report" in state and state["visual_analysis_report"]:
        visual_report = state["visual_analysis_report"]
        logger.debug("Found visual analysis report in state")
        
        # Handle both dict and object formats
        if isinstance(visual_report, dict):
            all_priority_urls = visual_report.get("all_priority_urls", [])
            logger.debug(f"Found {len(all_priority_urls)} URLs in dictionary format report")
        else:
            all_priority_urls = visual_report.all_priority_urls
            logger.debug(f"Found {len(all_priority_urls)} URLs in object format report")

        if all_priority_urls:
            high_priority_count = 0
            low_priority_count = 0
            
            for url in all_priority_urls:
                if url.priority <= 5:
                    url.mission_status = URLMissionStatus.IN_PROGRESS
                    high_priority_urls.append(url)
                    high_priority_count += 1
                    logger.debug(f"Selected high priority URL: {url.url} (priority: {url.priority})")
                else:
                    url.mission_status = URLMissionStatus.NOT_RELEVANT
                    low_priority_count += 1
                    
            logger.info(f"Filtered URLs: {high_priority_count} high priority, {low_priority_count} low priority")
        else:
            logger.info("No URLs found in visual analysis report")
    else:
        logger.info("No visual analysis report found in state")
        
    return {"high_priority_urls": high_priority_urls}


def save_url_analysis_state(state: URLInvestigationState):
    """
    Saving the final state to disk for debugging and tracking.
    """
    logger.info("Saving URL analysis final state")
    
    session_output_dir = state.get("output_directory", "output")
    session_id = state.get("session_id", "unknown_session")
    
    logger.debug(f"Session ID: {session_id}")
    logger.debug(f"Output directory: {session_output_dir}")

    # Create url investigation subdirectory
    url_investigation_directory = os.path.join(session_output_dir, "url_investigation")
    os.makedirs(url_investigation_directory, exist_ok=True)

    json_filename = f"url_investigation_state_session_{session_id}.json"
    json_path = os.path.join(url_investigation_directory, json_filename)
    
    logger.debug(f"Saving state to: {json_path}")

    try:
        dump_state_to_file(state, json_path)
        logger.info(f"URL analysis state saved to: {json_path}")
    except Exception as e:
        error_msg = f"Error writing URL analysis state to JSON: {e}"
        logger.error(error_msg, exc_info=True)
        state["errors"] = state.get("errors", []) + [error_msg]

    return {}
