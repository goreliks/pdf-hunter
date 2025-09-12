import os
import json
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_mcp_adapters.tools import load_mcp_tools
from .tools import domain_whois


from pdf_hunter.config import link_analysis_investigator_llm, link_analysis_analyst_llm
from .schemas import LinkAnalysisState, URLAnalysisResult, AnalystFindings
from .prompts import WFI_INVESTIGATOR_SYSTEM_PROMPT , WFI_ANALYST_SYSTEM_PROMPT, WFI_ANALYST_USER_PROMPT



# --- Node 1: Investigator ---
async def investigator_node(state: LinkAnalysisState) -> dict:
    """Performs the full dynamic, interactive investigation."""
    url_task = state["url_task"]
    output_dir = state["output_directory"]
    session = state["mcp_playwright_session"]
    
    print(f"\n--- [Investigator] Starting full pursuit for {url_task.url} ---")
    
    mcp_tools = await load_mcp_tools(session)
    all_tools = mcp_tools + [domain_whois]
    model_with_tools = link_analysis_investigator_llm.bind_tools(all_tools)

    workflow = StateGraph(MessagesState)
    workflow.add_node("llm", lambda s: {"messages": [model_with_tools.invoke(s["messages"])]})
    workflow.add_node("tools", ToolNode(all_tools))
    workflow.add_edge(START, "llm")
    workflow.add_conditional_edges("llm", tools_condition, {END: END, "tools": "tools"})
    workflow.add_edge("tools", "llm")
    investigator_graph = workflow.compile()
    
    initial_prompt = f"""
    Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    Begin your investigation.
    **URL:** {url_task.url}
    **Reason Flagged:** {url_task.reason}
    **Output Directory for Artifacts:** {os.path.abspath(output_dir)}
    """
    initial_state = { "messages": [ SystemMessage(content=WFI_INVESTIGATOR_SYSTEM_PROMPT), HumanMessage(content=initial_prompt) ] }
    
    final_state = await investigator_graph.ainvoke(initial_state)
    print("\n🕵️‍♂️✅ INVESTIGATION COMPLETE ✅🕵️‍♂️")
    return {"investigation_log": final_state["messages"]}
    

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
