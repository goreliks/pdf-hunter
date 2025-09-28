import os
import json
import asyncio
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from typing import Literal
from pdf_hunter.agents.image_analysis.schemas import URLMissionStatus
from .tools import domain_whois
from pdf_hunter.shared.utils.serializer import dump_state_to_file
from langgraph.constants import Send
from langgraph.graph import END


from pdf_hunter.config import url_investigation_investigator_llm, url_investigation_analyst_llm
from .schemas import URLInvestigationState, URLInvestigatorState, URLAnalysisResult, AnalystFindings
from .prompts import URL_INVESTIGATION_INVESTIGATOR_SYSTEM_PROMPT, URL_INVESTIGATION_ANALYST_SYSTEM_PROMPT, URL_INVESTIGATION_ANALYST_USER_PROMPT



async def investigate_url(state: URLInvestigatorState):
    """Analyze current state and decide on tool usage with MCP integration.

    This node uses an LLM to determine the next steps in the investigation,
    including whether to call a tool or proceed with analysis. It integrates
    with MCP for dynamic tool execution.
    """

    url_task = state["url_task"]
    session_output_dir = state["output_directory"]

    # Generate unique task ID for this investigation to ensure session isolation
    task_id = f"url_{abs(hash(url_task.url))}"

    # Create task-specific investigation directory under url investigation
    url_investigation_dir = os.path.join(session_output_dir, "url_investigation", "investigations")
    task_investigation_dir = os.path.join(url_investigation_dir, task_id)
    os.makedirs(task_investigation_dir, exist_ok=True)

    # Get the task-specific MCP session and load tools fresh each time
    from ...shared.utils.mcp_client import get_mcp_session
    from langchain_mcp_adapters.tools import load_mcp_tools
    session = await get_mcp_session(task_id, session_output_dir)
    mcp_tools = await load_mcp_tools(session)
    all_tools = mcp_tools + [domain_whois]
    model_with_tools = url_investigation_investigator_llm.bind_tools(all_tools)

    messages = state.get("investigation_logs", [])
    if not messages:
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
        # Get the LLM response asynchronously - proper async pattern
        llm_response = await model_with_tools.ainvoke(initial_messages)
        # Return both the initial messages AND the LLM response
        return {"investigation_logs": initial_messages + [llm_response]}
    else:
        # For subsequent calls, use existing messages and add only the new response
        llm_response = await model_with_tools.ainvoke(messages)
        return {"investigation_logs": [llm_response]}



async def execute_browser_tools(state: URLInvestigatorState):

    tool_calls = state["investigation_logs"][-1].tool_calls
    url_task = state["url_task"]
    session_output_dir = state["output_directory"]

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
        session = await get_mcp_session(task_id, session_output_dir)
        mcp_tools = await load_mcp_tools(session)
        tools = mcp_tools + [domain_whois]
        tool_by_name = {tool.name: tool for tool in tools}

        # Execute tool calls (sequentially for reliability)
        observations = []
        for tool_call in tool_calls:
            tool = tool_by_name[tool_call["name"]]
            try:
                if tool_call["name"] == "domain_whois":
                    # Use async invoke to prevent blocking
                    observation = await asyncio.to_thread(tool.invoke, tool_call["args"])
                else:
                    observation = await tool.ainvoke(tool_call["args"])
                observations.append(observation)
            except ToolException as e:
                # Handle tool exceptions gracefully (e.g., network errors, invalid URLs)
                error_msg = f"Tool execution failed: {str(e)}"
                print(f"⚠️ Warning: {error_msg}")
                observations.append(error_msg)
            except Exception as e:
                # Handle any other unexpected errors
                error_msg = f"Unexpected error in tool '{tool_call['name']}': {str(e)}"
                print(f"❌ Error: {error_msg}")
                observations.append(error_msg)

        tool_outputs = [
            ToolMessage(
                content=observation,
                name=tool_call["name"],
                tool_call_id=tool_call["id"]
            )
            for observation, tool_call in zip(observations, tool_calls)
        ]

        return tool_outputs
    
    messages = await execute_tools()

    # Return the messages to be added to the investigation_logs
    # Since add_messages handles sequences, we can return the list
    return {"investigation_logs": messages}



# --- Node 2: Analyst ---
async def analyze_url_content(state: URLInvestigatorState) -> dict:
    """Synthesizes all evidence and assembles the final report."""
    url_task = state["url_task"]
    investigation_log = state["investigation_logs"]

    print("\n--- [Analyst] Starting synthesis of all evidence ---")

    analyst_llm = url_investigation_analyst_llm.with_structured_output(AnalystFindings)
    analyst_prompt = URL_INVESTIGATION_ANALYST_USER_PROMPT.format(
        current_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        initial_briefing_json=url_task.model_dump_json(indent=2),
        investigation_log_json=json.dumps([msg.model_dump() for msg in investigation_log], indent=2)
    )
    analyst_findings = await analyst_llm.ainvoke([
        SystemMessage(content=URL_INVESTIGATION_ANALYST_SYSTEM_PROMPT),
        HumanMessage(content=analyst_prompt)
    ])

    url_task.mission_status = (
        URLMissionStatus.COMPLETED if analyst_findings.mission_status == "completed"
        else URLMissionStatus.FAILED
    )

    link_analysis_final_report = URLAnalysisResult(
        initial_url=url_task,
        full_investigation_log=[msg.model_dump() for msg in investigation_log],
        analyst_findings=analyst_findings
    )
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

    if last_message.tool_calls:
        return "execute_browser_tools"
    return "analyze_url_content"


def route_url_analysis(state: URLInvestigationState):
    """
    Dispatch the link analysis tasks based on high priority URLs from visual analysis.
    Uses Send to parallelize URL analysis across multiple instances.
    """
    high_priority_urls = state.get("high_priority_urls", [])
    if high_priority_urls:
        return [Send("conduct_link_analysis", {
            "url_task": url,
            "output_directory": state["output_directory"]
        }) for url in high_priority_urls]
    
    return "save_url_analysis_state"


def filter_high_priority_urls(state: URLInvestigationState):
    """
    Filter and return only high priority URLs from the visual analysis report.
    """
    # Create url investigation investigations directory
    session_output_dir = state.get("output_directory")
    high_priority_urls = []
    if session_output_dir:
        url_investigation_dir = os.path.join(session_output_dir, "url_investigation", "investigations")
        os.makedirs(url_investigation_dir, exist_ok=True)

    if "visual_analysis_report" in state and state["visual_analysis_report"]:
        visual_report = state["visual_analysis_report"]
        # Handle both dict and object formats
        if isinstance(visual_report, dict):
            all_priority_urls = visual_report.get("all_priority_urls", [])
        else:
            all_priority_urls = visual_report.all_priority_urls

        if all_priority_urls:
            for url in all_priority_urls:
                if url.priority <= 5:
                    url.mission_status = URLMissionStatus.IN_PROGRESS
                    high_priority_urls.append(url)
                else:
                    url.mission_status = URLMissionStatus.NOT_RELEVANT
    return {"high_priority_urls": high_priority_urls}


def save_url_analysis_state(state: URLInvestigationState):
    """
    Saving the final state to disk for debugging and tracking.
    """
    session_output_dir = state.get("output_directory", "output")
    session_id = state.get("session_id", "unknown_session")

    # Create url investigation subdirectory
    url_investigation_directory = os.path.join(session_output_dir, "url_investigation")
    os.makedirs(url_investigation_directory, exist_ok=True)

    json_filename = f"url_investigation_state_session_{session_id}.json"
    json_path = os.path.join(url_investigation_directory, json_filename)

    try:
        dump_state_to_file(state, json_path)
        print(f"--- Link analysis state saved to: {json_path} ---")
    except Exception as e:
        state["errors"] = state.get("errors", []) + [f"Error writing link analysis state to JSON: {e} ---"]

    return {}
