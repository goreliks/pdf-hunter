import os
import json
import asyncio
from datetime import datetime
from loguru import logger
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from typing import Literal
from pdf_hunter.agents.image_analysis.schemas import URLMissionStatus
from .tools import domain_whois
from pdf_hunter.shared.utils.serializer import dump_state_to_file
from langgraph.types import Send
from langgraph.graph import END
from pdf_hunter.config import THINKING_TOOL_ENABLED, URL_INVESTIGATION_PRIORITY_LEVEL
from pdf_hunter.config.execution_config import LLM_TIMEOUT_TEXT


from pdf_hunter.config import url_investigation_investigator_llm, url_investigation_analyst_llm
from .schemas import URLInvestigationState, URLInvestigatorState, URLAnalysisResult, AnalystFindings
from .prompts import URL_INVESTIGATION_INVESTIGATOR_SYSTEM_PROMPT, URL_INVESTIGATION_ANALYST_SYSTEM_PROMPT, URL_INVESTIGATION_ANALYST_USER_PROMPT, URL_INVESTIGATION_LOG_SUMMARIZATION_PROMPT

# Helper function to load MCP tools asynchronously
async def load_mcp_tools_async(session):
    """
    Load MCP tools in a non-blocking way by moving the import to a separate thread.
    
    Args:
        session: The MCP session to use
        
    Returns:
        The loaded MCP tools
    """
    def _load_tools():
        from langchain_mcp_adapters.tools import load_mcp_tools
        return load_mcp_tools
    
    load_mcp_tools_fn = await asyncio.to_thread(_load_tools)
    return await load_mcp_tools_fn(session)



async def investigate_url(state: URLInvestigatorState):
    """Analyze current state and decide on tool usage with MCP integration.

    This node uses an LLM to determine the next steps in the investigation,
    including whether to call a tool or proceed with analysis. It integrates
    with MCP for dynamic tool execution.
    """
    
    try:
        url_task = state.get("url_task")
        session_output_dir = state.get("output_directory")
        
        # Validate required inputs
        if not url_task:
            raise ValueError("url_task is required")
        if not session_output_dir:
            raise ValueError("output_directory is required")
        
        logger.info(
            f"🔍 Starting URL investigation: {url_task.url}",
            agent="URLInvestigation",
            node="investigate_url",
            event_type="INVESTIGATION_START",
            url=url_task.url,
            priority=url_task.priority
        )
        logger.debug(
            f"URL priority: {url_task.priority}, source context: {getattr(url_task, 'source_context', 'None')}",
            agent="URLInvestigation",
            node="investigate_url"
        )

        # Generate unique task ID for this investigation to ensure session isolation
        task_id = f"url_{abs(hash(url_task.url))}"
        logger.debug(f"Generated task ID: {task_id}", agent="URLInvestigation", node="investigate_url")

        # MCP Playwright will automatically create task_url_{task_id} directory for screenshots and traces
        # Get the task-specific MCP session and load tools fresh each time
        from ...shared.utils.mcp_client import get_mcp_session
        
        logger.debug(f"Getting MCP session for task: {task_id}", agent="URLInvestigation", node="investigate_url")
        session = await get_mcp_session(task_id, session_output_dir)
        logger.debug("Loading MCP tools", agent="URLInvestigation", node="investigate_url")
        mcp_tools = await load_mcp_tools_async(session)
        all_tools = mcp_tools + [domain_whois]
        if THINKING_TOOL_ENABLED:
            from pdf_hunter.shared.tools import think_tool
            all_tools.append(think_tool)
            logger.debug("Thinking tool enabled and added to toolset", agent="URLInvestigation", node="investigate_url")
        logger.debug(f"Loaded {len(all_tools)} tools for investigation", agent="URLInvestigation", node="investigate_url")
        model_with_tools = url_investigation_investigator_llm.bind_tools(all_tools)

        messages = state.get("investigation_logs", [])
        if not messages:
            logger.info("🆕 Starting new investigation chain", agent="URLInvestigation", node="investigate_url", event_type="CHAIN_START")
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
            logger.debug("Created initial investigation prompt", agent="URLInvestigation", node="investigate_url")
            
            # Get the LLM response asynchronously - proper async pattern
            logger.debug("Invoking investigator LLM", agent="URLInvestigation", node="investigate_url")
            llm_response = await model_with_tools.ainvoke(initial_messages)
            logger.debug("Received LLM response for initial investigation", agent="URLInvestigation", node="investigate_url")
            
            # Return both the initial messages AND the LLM response
            return {"investigation_logs": initial_messages + [llm_response]}
        
        else:
            # For subsequent calls, use existing messages and add only the new response
            logger.debug(f"🔄 Continuing investigation chain, turn {len(messages) // 2}", agent="URLInvestigation", node="investigate_url")
            llm_response = await model_with_tools.ainvoke(messages)
            logger.debug("Received LLM response for continued investigation", agent="URLInvestigation", node="investigate_url")
            return {"investigation_logs": [llm_response]}
    
    except Exception as e:
        error_msg = f"Error in investigate_url: {e}"
        logger.error(error_msg, agent="URLInvestigation", node="investigate_url", event_type="ERROR", exc_info=True)
        return {"errors": [error_msg]}



async def execute_browser_tools(state: URLInvestigatorState):
    """Execute tool calls using browser automation through MCP."""
    
    try:
        # Safety check to handle potential issues with tool_calls format
        investigation_logs = state.get("investigation_logs", [])
        if not investigation_logs:
            logger.warning("No investigation logs found", agent="URLInvestigation", node="execute_browser_tools")
            return {"errors": ["No investigation logs available for tool execution"]}
            
        last_message = investigation_logs[-1]
        if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            logger.warning("No tool calls found in the last message", agent="URLInvestigation", node="execute_browser_tools")
            return {"investigation_logs": [ToolMessage(content="No tool calls were found to execute.", tool_call_id="none")]}
        
        tool_calls = last_message.tool_calls
        url_task = state.get("url_task")
        session_output_dir = state.get("output_directory")
        
        # Validate required inputs
        if not url_task:
            raise ValueError("url_task is required")
        if not session_output_dir:
            raise ValueError("output_directory is required")
        
        logger.info(
            f"🔧 Executing {len(tool_calls)} tool call(s) for: {url_task.url}",
            agent="URLInvestigation",
            node="execute_browser_tools",
            event_type="TOOL_EXECUTION_START",
            tool_count=len(tool_calls),
            url=url_task.url
        )

        # Generate the same task ID as used in investigate_url for session consistency
        task_id = f"url_{abs(hash(url_task.url))}"

        # MCP Playwright will automatically create task_url_{task_id} directory for screenshots and traces

        async def execute_tools():
            from langchain_core.tools.base import ToolException
            
            # Get the task-specific MCP session and load tools fresh each time
            from ...shared.utils.mcp_client import get_mcp_session
            
            logger.debug(f"Getting MCP session for tool execution: {task_id}", agent="URLInvestigation", node="execute_browser_tools")
            session = await get_mcp_session(task_id, session_output_dir)
            logger.debug("Loading MCP tools for execution", agent="URLInvestigation", node="execute_browser_tools")
            mcp_tools = await load_mcp_tools_async(session)
            tools = mcp_tools + [domain_whois]
            if THINKING_TOOL_ENABLED:
                from pdf_hunter.shared.tools.think_tool import think_tool
                tools.append(think_tool)
                logger.debug("Thinking tool enabled and added to execution toolset", agent="URLInvestigation", node="execute_browser_tools")
            logger.debug(f"Loaded {len(tools)} tools for execution", agent="URLInvestigation", node="execute_browser_tools")
            tool_by_name = {tool.name: tool for tool in tools}

            # Execute tool calls (sequentially for reliability)
            observations = []
            for tool_call in tool_calls:
                # Handle both dict and object formats for tool_call
                tool_name = tool_call.get("name") if isinstance(tool_call, dict) else getattr(tool_call, "name")
                logger.info(f"🔧 Executing tool: {tool_name}", agent="URLInvestigation", node="execute_browser_tools", event_type="TOOL_CALL", tool_name=tool_name)

                try:
                    tool = tool_by_name[tool_name]
                    
                    # Handle both dict and object formats for tool_call args
                    tool_args = tool_call.get("args") if isinstance(tool_call, dict) else getattr(tool_call, "args")

                    if tool_name == "domain_whois":
                        # Use async invoke to prevent blocking
                        observation = await asyncio.to_thread(tool.invoke, tool_args)
                    elif tool_name == "think_tool":
                        # Use async invoke to prevent blocking
                        observation = await asyncio.to_thread(tool.invoke, tool_args)
                        # Log the strategic reflection at INFO level
                        reflection_text = tool_args.get("reflection", "") if isinstance(tool_args, dict) else getattr(tool_args, "reflection", "")
                        if reflection_text:
                            logger.info(
                                f"💭 Strategic Reflection: {reflection_text}",
                                agent="URLInvestigation",
                                node="execute_browser_tools",
                                event_type="STRATEGIC_THINKING",
                                tool_name=tool_name,
                                reflection=reflection_text
                            )
                    else:
                        # MCP browser tools
                        observation = await tool.ainvoke(tool_args)
                        
                    logger.info(f"✅ Tool {tool_name} executed successfully", agent="URLInvestigation", node="execute_browser_tools", event_type="TOOL_SUCCESS", tool_name=tool_name)
                    observations.append(observation)
                    
                except ToolException as e:
                    # Handle tool exceptions gracefully (e.g., network errors, invalid URLs)
                    error_msg = f"Tool execution failed: {str(e)}"
                    # Escape HTML/XML tags to prevent Loguru colorizer errors
                    safe_error = str(e).replace('<', '{{').replace('>', '}}')
                    logger.warning(f"⚠️ Tool {tool_name} execution failed: {safe_error}", agent="URLInvestigation", node="execute_browser_tools", event_type="TOOL_FAILURE", tool_name=tool_name)
                    observations.append(error_msg)
                    
                except Exception as e:
                    # Handle any other unexpected errors
                    error_msg = f"Unexpected error in tool '{tool_name}': {str(e)}"
                    # Escape HTML/XML tags to prevent Loguru colorizer errors
                    safe_error = str(e).replace('<', '{{').replace('>', '}}')
                    logger.error(f"Unexpected error in tool {tool_name}: {safe_error}", agent="URLInvestigation", node="execute_browser_tools", event_type="TOOL_ERROR", tool_name=tool_name, exc_info=True)
                    observations.append(error_msg)

            # Create tool output messages, handling both dict and object formats
            tool_outputs = []
            for observation, tool_call in zip(observations, tool_calls):
                tool_name = tool_call.get("name") if isinstance(tool_call, dict) else getattr(tool_call, "name")
                tool_call_id = tool_call.get("id") if isinstance(tool_call, dict) else getattr(tool_call, "id")
                tool_outputs.append(
                    ToolMessage(
                        content=observation,
                        name=tool_name,
                        tool_call_id=tool_call_id
                    )
                )
            
            logger.debug(f"Created {len(tool_outputs)} tool messages", agent="URLInvestigation", node="execute_browser_tools")
            return tool_outputs
        
        logger.debug("Executing all tools", agent="URLInvestigation", node="execute_browser_tools")
        messages = await execute_tools()
        logger.info(
            f"✅ Completed execution of {len(messages)} tools",
            agent="URLInvestigation",
            node="execute_browser_tools",
            event_type="TOOL_EXECUTION_COMPLETE",
            tool_count=len(messages)
        )

        # Return the messages to be added to the investigation_logs
        # Since add_messages handles sequences, we can return the list
        return {"investigation_logs": messages}
    
    except Exception as e:
        error_msg = f"Error in execute_browser_tools: {e}"
        logger.error(error_msg, agent="URLInvestigation", node="execute_browser_tools", event_type="ERROR", exc_info=True)
        return {"errors": [error_msg]}


async def summarize_investigation_log(investigation_log: list, mission: dict) -> str:
    """
    Summarize verbose investigation log for analyst consumption.

    This compresses the log by removing verbose accessibility trees while preserving
    all investigator decisions, tool calls, and key findings.

    Args:
        investigation_log: List of BaseMessage objects from investigation
        mission: Mission context dict with reason_flagged

    Returns:
        Compressed narrative summary as JSON string (for analyst prompt)
    """
    from pdf_hunter.config import report_generator_llm  # Use existing summarization-capable model

    logger.debug(
        f"Summarizing investigation log: {len(investigation_log)} messages",
        agent="URLInvestigation",
        node="summarize_investigation_log",
        message_count=len(investigation_log)
    )

    # Build readable log preview
    log_text_parts = []
    ai_turn = 0

    for i, msg in enumerate(investigation_log):
        if msg.type == "ai":
            ai_turn += 1
            log_text_parts.append(f"\n=== Investigator Turn {ai_turn} ===")

            # Include investigator's reasoning if present
            if hasattr(msg, "content") and msg.content:
                reasoning = msg.content[:500] if len(msg.content) > 500 else msg.content
                log_text_parts.append(f"Reasoning: {reasoning}")

            # Include tool calls
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_names = [tc.get("name", "unknown") if isinstance(tc, dict) else getattr(tc, "name", "unknown") for tc in msg.tool_calls]
                log_text_parts.append(f"Tools called: {', '.join(tool_names)}")

        elif msg.type == "tool":
            tool_name = getattr(msg, "name", "unknown")
            log_text_parts.append(f"\nTool: {tool_name}")

            # Include preview of tool response (first 500 chars)
            content_preview = msg.content[:500] + "..." if len(msg.content) > 500 else msg.content
            log_text_parts.append(f"Response preview: {content_preview}")

    full_log_text = "\n".join(log_text_parts)

    # Build summarization prompt from template
    summary_prompt = URL_INVESTIGATION_LOG_SUMMARIZATION_PROMPT.format(
        mission_reason=mission.get('reason_flagged', 'URL investigation'),
        investigation_log=full_log_text
    )

    try:
        logger.debug("Invoking LLM for log summarization", agent="URLInvestigation", node="summarize_investigation_log")
        response = await asyncio.wait_for(
            report_generator_llm.ainvoke([HumanMessage(content=summary_prompt)]),
            timeout=LLM_TIMEOUT_TEXT
        )

        summarized_narrative = response.content

        logger.info(
            f"✅ Investigation log summarized: {len(full_log_text)} chars → {len(summarized_narrative)} chars",
            agent="URLInvestigation",
            node="summarize_investigation_log",
            original_size=len(full_log_text),
            summarized_size=len(summarized_narrative),
            compression_ratio=f"{(1 - len(summarized_narrative)/len(full_log_text))*100:.1f}%"
        )

        return summarized_narrative

    except Exception as e:
        logger.warning(
            f"Failed to summarize investigation log: {e}. Falling back to full log.",
            agent="URLInvestigation",
            node="summarize_investigation_log",
            exc_info=True
        )
        # Fallback: return full log as JSON (analyst still works, just with more tokens)
        return json.dumps([msg.model_dump() for msg in investigation_log], indent=2)


# --- Node 2: Analyst ---
async def analyze_url_content(state: URLInvestigatorState) -> dict:
    """Synthesizes all evidence and assembles the final report."""
    
    try:
        url_task = state.get("url_task")
        investigation_log = state.get("investigation_logs", [])
        
        # Validate required inputs
        if not url_task:
            raise ValueError("url_task is required")
        if not investigation_log:
            raise ValueError("investigation_logs is required")

        logger.info(
            f"📊 Starting analysis synthesis for: {url_task.url}",
            agent="URLInvestigation",
            node="analyze_url_content",
            event_type="ANALYSIS_START",
            url=url_task.url,
            log_messages=len(investigation_log)
        )

        analyst_llm = url_investigation_analyst_llm.with_structured_output(AnalystFindings)

        # Summarize investigation log if it's long (more than ~2-3 turns = >5 messages)
        # This reduces context window usage for the analyst without losing key findings
        if len(investigation_log) > 5:
            logger.debug(
                f"Investigation log is long ({len(investigation_log)} messages), summarizing for analyst",
                agent="URLInvestigation",
                node="analyze_url_content",
                message_count=len(investigation_log)
            )
            investigation_log_json = await summarize_investigation_log(
                investigation_log,
                url_task.model_dump()  # Pass mission context
            )
        else:
            logger.debug(
                f"Investigation log is short ({len(investigation_log)} messages), no summarization needed",
                agent="URLInvestigation",
                node="analyze_url_content",
                message_count=len(investigation_log)
            )
            investigation_log_json = json.dumps([msg.model_dump() for msg in investigation_log], indent=2)

        logger.debug("Creating analyst prompt", agent="URLInvestigation", node="analyze_url_content")
        analyst_prompt = URL_INVESTIGATION_ANALYST_USER_PROMPT.format(
            current_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            initial_briefing_json=url_task.model_dump_json(indent=2),
            investigation_log_json=investigation_log_json
        )
        
        logger.debug("Invoking analyst LLM for findings synthesis", agent="URLInvestigation", node="analyze_url_content")
        # Add timeout protection to prevent infinite hangs on analyst LLM calls
        analyst_findings = await asyncio.wait_for(
            analyst_llm.ainvoke([
                SystemMessage(content=URL_INVESTIGATION_ANALYST_SYSTEM_PROMPT),
                HumanMessage(content=analyst_prompt)
            ]),
            timeout=LLM_TIMEOUT_TEXT
        )

        new_status = URLMissionStatus.COMPLETED if analyst_findings.mission_status == "completed" else URLMissionStatus.FAILED
        url_task.mission_status = new_status

        summary_preview = analyst_findings.summary[:300] + "..." if len(analyst_findings.summary) > 300 else analyst_findings.summary
        logger.info(
            f"📊 Analysis Complete | Verdict: {analyst_findings.verdict} | Confidence: {analyst_findings.confidence:.1%} | Status: {new_status.value} | Summary: {summary_preview}",
            agent="URLInvestigation",
            node="analyze_url_content",
            event_type="ANALYSIS_COMPLETE",
            url=url_task.url,
            verdict=analyst_findings.verdict,
            confidence=analyst_findings.confidence,
            mission_status=new_status.value,
            final_url=analyst_findings.final_url,
            summary=analyst_findings.summary,
            detected_threats=analyst_findings.detected_threats,
            screenshot_count=len(analyst_findings.screenshot_paths)
        )

        link_analysis_final_report = URLAnalysisResult(
            initial_url=url_task,
            full_investigation_log=[msg.model_dump() for msg in investigation_log],
            analyst_findings=analyst_findings
        )
        
        logger.debug("Generated final URL analysis report", agent="URLInvestigation", node="analyze_url_content")
        return {"link_analysis_final_report": link_analysis_final_report}
    
    except asyncio.TimeoutError:
        error_msg = f"Error in analyze_url_content: Analyst LLM call timed out after {LLM_TIMEOUT_TEXT} seconds for URL: {url_task.url}"
        logger.error(
            "Error in analyze_url_content: Analyst LLM call timed out after {} seconds for URL: {}",
            LLM_TIMEOUT_TEXT,
            url_task.url,
            agent="URLInvestigation",
            node="analyze_url_content",
            event_type="ERROR",
            timeout_seconds=LLM_TIMEOUT_TEXT,
            url=url_task.url,
            exc_info=True
        )
        return {"errors": [error_msg]}
    except Exception as e:
        error_msg = f"Error in analyze_url_content: {type(e).__name__}: {e}"
        logger.error(
            "Error in analyze_url_content: {}: {}",
            type(e).__name__,
            str(e),
            agent="URLInvestigation",
            node="analyze_url_content",
            event_type="ERROR",
            exc_info=True
        )
        return {"errors": [error_msg]}


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
        logger.debug(f"URL {url}: Tool calls found, continuing with tool execution", agent="URLInvestigation", node="should_continue")
        return "execute_browser_tools"
    
    logger.info(f"URL {url}: No more tool calls, proceeding to analysis", agent="URLInvestigation", node="should_continue", event_type="ROUTING_TO_ANALYSIS")
    return "analyze_url_content"


def route_url_analysis(state: URLInvestigationState):
    """
    Dispatch the link analysis tasks based on high priority URLs from visual analysis.
    Uses Send to parallelize URL analysis across multiple instances.
    """
    high_priority_urls = state.get("high_priority_urls", [])
    
    if high_priority_urls:
        logger.info(
            f"🚀 Dispatching {len(high_priority_urls)} URL investigations in parallel",
            agent="URLInvestigation",
            node="route_url_analysis",
            event_type="PARALLEL_DISPATCH",
            url_count=len(high_priority_urls)
        )
        
        for url in high_priority_urls:
            logger.debug(f"Preparing to analyze URL: {url.url} (priority: {url.priority})", agent="URLInvestigation", node="route_url_analysis")
            
        return [Send("conduct_link_analysis", {
            "url_task": url,
            "output_directory": state["output_directory"]
        }) for url in high_priority_urls]
    
    logger.info("No high priority URLs found for analysis", agent="URLInvestigation", node="route_url_analysis", event_type="NO_URLS_TO_ANALYZE")
    return "save_url_analysis_state"


async def filter_high_priority_urls(state: URLInvestigationState):
    """
    Filter and return only high priority URLs from the visual analysis report.
    """
    logger.info("🔎 Filtering high priority URLs from visual analysis", agent="URLInvestigation", node="filter_high_priority_urls", event_type="FILTER_START")
    
    try:
        high_priority_urls = []
        
        # MCP Playwright will automatically create url_investigation/task_url_* directories for each investigation

        if "visual_analysis_report" in state and state["visual_analysis_report"]:
            visual_report = state["visual_analysis_report"]
            logger.debug("Found visual analysis report in state", agent="URLInvestigation", node="filter_high_priority_urls")
            
            # Handle both dict and object formats
            if isinstance(visual_report, dict):
                all_priority_urls = visual_report.get("all_priority_urls", [])
                logger.debug(f"Found {len(all_priority_urls)} URLs in dictionary format report", agent="URLInvestigation", node="filter_high_priority_urls")
            else:
                all_priority_urls = visual_report.all_priority_urls
                logger.debug(f"Found {len(all_priority_urls)} URLs in object format report", agent="URLInvestigation", node="filter_high_priority_urls")

            if all_priority_urls:
                high_priority_count = 0
                low_priority_count = 0
                
                for url in all_priority_urls:
                    if url.priority <= URL_INVESTIGATION_PRIORITY_LEVEL:
                        url.mission_status = URLMissionStatus.IN_PROGRESS
                        high_priority_urls.append(url)
                        high_priority_count += 1
                        logger.debug(f"Selected high priority URL: {url.url} (priority: {url.priority})", agent="URLInvestigation", node="filter_high_priority_urls")
                    else:
                        url.mission_status = URLMissionStatus.NOT_RELEVANT
                        low_priority_count += 1
                        
                logger.info(
                    f"🔎 Filtered URLs: {high_priority_count} high priority (≤{URL_INVESTIGATION_PRIORITY_LEVEL}), {low_priority_count} low priority (>{URL_INVESTIGATION_PRIORITY_LEVEL}) out of {len(all_priority_urls)} total",
                    agent="URLInvestigation",
                    node="filter_high_priority_urls",
                    event_type="FILTER_COMPLETE",
                    high_priority_count=high_priority_count,
                    low_priority_count=low_priority_count,
                    total_urls=len(all_priority_urls)
                )
            else:
                logger.info("No URLs found in visual analysis report", agent="URLInvestigation", node="filter_high_priority_urls")
        else:
            logger.info("No visual analysis report found in state", agent="URLInvestigation", node="filter_high_priority_urls")
            
        return {"high_priority_urls": high_priority_urls}
    
    except Exception as e:
        error_msg = f"Error in filter_high_priority_urls: {e}"
        logger.error(error_msg, agent="URLInvestigation", node="filter_high_priority_urls", event_type="ERROR", exc_info=True)
        return {"errors": [error_msg]}


async def save_url_analysis_state(state: URLInvestigationState):
    """
    Saving the final state to disk for debugging and tracking.
    """
    logger.info("💾 Saving URL analysis final state", agent="URLInvestigation", node="save_url_analysis_state", event_type="SAVE_START")
    
    try:
        session_output_dir = state.get("output_directory", "output")
        session_id = state.get("session_id", "unknown_session")
        
        logger.debug(f"Session ID: {session_id} | Output: {session_output_dir}", agent="URLInvestigation", node="save_url_analysis_state")

        # Create url investigation subdirectory
        url_investigation_directory = os.path.join(session_output_dir, "url_investigation")
        await asyncio.to_thread(os.makedirs, url_investigation_directory, exist_ok=True)

        json_filename = f"url_investigation_state_session_{session_id}.json"
        json_path = os.path.join(url_investigation_directory, json_filename)
        
        logger.debug(f"Saving state to: {json_path}", agent="URLInvestigation", node="save_url_analysis_state")
        await dump_state_to_file(state, json_path)
        
        # Count results
        results_count = len(state.get("link_analysis_final_reports", []))
        logger.info(
            f"💾 URL analysis state saved: {results_count} investigations complete",
            agent="URLInvestigation",
            node="save_url_analysis_state",
            event_type="SAVE_COMPLETE",
            file_path=json_path,
            investigation_count=results_count,
            session_id=session_id
        )

        return {}
    
    except Exception as e:
        error_msg = f"Error in save_url_analysis_state: {e}"
        logger.error(error_msg, agent="URLInvestigation", node="save_url_analysis_state", event_type="ERROR", exc_info=True)
        return {"errors": [error_msg]}
