import os
import json
import asyncio
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from typing import Literal
from .tools import domain_whois


from pdf_hunter.config import link_analysis_investigator_llm, link_analysis_analyst_llm
from .schemas import LinkAnalysisState, URLAnalysisResult, AnalystFindings
from .prompts import WFI_INVESTIGATOR_SYSTEM_PROMPT , WFI_ANALYST_SYSTEM_PROMPT, WFI_ANALYST_USER_PROMPT



async def llm_call(state: LinkAnalysisState):
    """Analyze current state and decide on tool usage with MCP integration.

    This node uses an LLM to determine the next steps in the investigation,
    including whether to call a tool or proceed with analysis. It integrates
    with MCP for dynamic tool execution.
    """

    url_task = state["url_task"]
    output_dir = state["output_directory"]
    
    # Get the persistent MCP session and load tools fresh each time
    from ...shared.utils.mcp_client import get_mcp_session
    from langchain_mcp_adapters.tools import load_mcp_tools
    session = await get_mcp_session()
    mcp_tools = await load_mcp_tools(session)
    all_tools = mcp_tools + [domain_whois]
    model_with_tools = link_analysis_investigator_llm.bind_tools(all_tools)

    messages = state.get("investigation_log", [])
    if not messages:
        # Get absolute path in a non-blocking way
        abs_output_dir = await asyncio.to_thread(os.path.abspath, output_dir)
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
        **Output Directory for Artifacts:** {abs_output_dir}
        
        **IMPORTANT:** This URL was extracted from a PDF document, not discovered on a website. The PDF may have used social engineering tactics (like fake verification prompts) to trick users into visiting this URL. Your investigation should focus on where this URL leads and whether it's part of a larger attack chain.
        """
        initial_messages = [ SystemMessage(content=WFI_INVESTIGATOR_SYSTEM_PROMPT), HumanMessage(content=initial_prompt) ]
        # Get the LLM response asynchronously - proper async pattern
        llm_response = await model_with_tools.ainvoke(initial_messages)
        # Return both the initial messages AND the LLM response
        return {"investigation_log": initial_messages + [llm_response]}
    else:
        # For subsequent calls, use existing messages and add only the new response
        llm_response = await model_with_tools.ainvoke(messages)
        return {"investigation_log": llm_response}



async def tool_node(state: LinkAnalysisState):

    tool_calls = state["investigation_log"][-1].tool_calls

    async def execute_tools():
        from langchain_core.tools.base import ToolException
        
        # Get the persistent MCP session and load tools fresh each time
        from ...shared.utils.mcp_client import get_mcp_session
        from langchain_mcp_adapters.tools import load_mcp_tools
        session = await get_mcp_session()
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

    # Return the messages to be added to the investigation_log
    # Since add_messages handles sequences, we can return the list
    return {"investigation_log": messages}



# --- Node 2: Analyst ---
async def analyst_node(state: LinkAnalysisState) -> dict:
    """Synthesizes all evidence and assembles the final report."""
    url_task = state["url_task"]
    investigation_log = state["investigation_log"]

    print("\n--- [Analyst] Starting synthesis of all evidence ---")

    analyst_llm = link_analysis_analyst_llm.with_structured_output(AnalystFindings)
    analyst_prompt = WFI_ANALYST_USER_PROMPT.format(
        current_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        initial_briefing_json=url_task.model_dump_json(indent=2),
        investigation_log_json=json.dumps([msg.model_dump() for msg in investigation_log], indent=2)
    )
    analyst_findings = await analyst_llm.ainvoke([
        SystemMessage(content=WFI_ANALYST_SYSTEM_PROMPT),
        HumanMessage(content=analyst_prompt)
    ])

    link_analysis_final_report = URLAnalysisResult(
        initial_url=url_task,
        full_investigation_log=[msg.model_dump() for msg in investigation_log],
        analyst_findings=analyst_findings
    )
    return {"link_analysis_final_report": link_analysis_final_report}


def should_continue(state: LinkAnalysisState) -> Literal["tool_node", "analyst_node"]:
    """Determine whether to continue with tool execution or proceed to analysis.
    This function checks the latest messages in the investigation log to see if
    any tools were called. If tools were called, it returns "tool_node" to continue
    executing tools. If no tools were called, it returns "analyst_node" to proceed
    to the analysis phase.
    """
    messages = state["investigation_log"]
    last_message = messages[-1]

    if last_message.tool_calls:
        return "tool_node"
    return "analyst_node"
