from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langgraph.prebuilt import ToolNode
from langgraph.errors import GraphRecursionError
from .schemas import InvestigatorState, InvestigatorOutputState, FileAnalysisState, FileAnalysisInputState, FileAnalysisOutputState, MissionStatus
from .nodes import file_analyzer, identify_suspicious_elements, create_analysis_tasks, assign_analysis_tasks, review_analysis_results, summarize_file_analysis
from .tools import pdf_parser_tools
from langgraph.prebuilt import tools_condition
from loguru import logger
from pdf_hunter.config import FILE_ANALYSIS_CONFIG, FILE_ANALYSIS_INVESTIGATOR_CONFIG



investigator_builder = StateGraph(InvestigatorState, output_schema=InvestigatorOutputState)

investigator_builder.add_node("investigation", file_analyzer)
investigator_builder.add_node("tools", ToolNode(pdf_parser_tools))

investigator_builder.add_edge(START, "investigation")
investigator_builder.add_edge("tools", "investigation")

investigator_builder.add_conditional_edges(
    "investigation",
    tools_condition,
)

investigator_graph = investigator_builder.compile()
investigator_graph = investigator_graph.with_config(FILE_ANALYSIS_INVESTIGATOR_CONFIG)


# Create a wrapper that ensures outputs are aggregated properly
async def run_file_analysis(state: dict):
    """
    Wrapper for the investigator subgraph that ensures outputs are collected
    into the completed_investigations list.
    """
    
    try:
        mission = state.get("mission")
        mission_id = mission.mission_id if mission else "unknown"
        threat_type = mission.threat_type if mission else "unknown"
        
        if mission:
            logger.debug(
                f"Starting investigator subgraph for {mission_id}",
                agent="FileAnalysis",
                node="run_file_analysis",
                mission_id=mission_id,
                threat_type=threat_type
            )
        
        # Run the investigator subgraph
        result = await investigator_graph.ainvoke(state)
        
        if result.get("mission_report"):
            logger.debug(
                f"Investigation completed: {mission_id} -> {result['mission_report'].final_status}",
                agent="FileAnalysis",
                node="run_file_analysis",
                mission_id=mission_id,
                final_status=result['mission_report'].final_status.value
            )
        
        # The result should contain the fields from InvestigatorOutputState
        # We need to wrap it in a list so it gets aggregated via operator.add
        return {
            "completed_investigations": [result]  # This will be aggregated
        }
    
    except GraphRecursionError as e:
        # Handle recursion limit specifically - mark mission as blocked
        error_msg = f"Mission {mission_id} hit recursion limit - too complex or stuck in loop"
        logger.warning(
            f"⚠️ {error_msg}",
            agent="FileAnalysis",
            node="run_file_analysis",
            event_type="RECURSION_LIMIT",
            mission_id=mission_id
        )
        
        # Return a partial investigation result marking the mission as blocked
        from .schemas import EvidenceGraph
        blocked_result = {
            "mission": mission,
            "mission_report": None,  # No report generated
            "errors": [error_msg],
            "messages": state.get("messages", [])
        }
        
        return {
            "completed_investigations": [blocked_result],
            "errors": [error_msg]
        }
    
    except Exception as e:
        error_msg = f"Error in run_file_analysis: {e}"
        logger.error(
            error_msg,
            agent="FileAnalysis",
            node="run_file_analysis",
            event_type="ERROR",
            exc_info=True
        )
        return {"errors": [error_msg]}

# Add the wrapper as the node instead of the raw subgraph


static_analysis_builder = StateGraph(FileAnalysisState, input_schema=FileAnalysisInputState, output_schema=FileAnalysisOutputState)

# Add nodes to static_analysis_builder
static_analysis_builder.add_node("identify_suspicious_elements", identify_suspicious_elements)
static_analysis_builder.add_node("create_analysis_tasks", create_analysis_tasks)
# static_analysis_builder.add_node("conduct_investigation", investigator_graph)
static_analysis_builder.add_node("run_file_analysis", run_file_analysis)
# static_analysis_builder.add_node("reducer_node", reducer_node)
static_analysis_builder.add_node("review_analysis_results", review_analysis_results)
static_analysis_builder.add_node("summarize_file_analysis", summarize_file_analysis)

# Add edges to static_analysis_builder (not investigator_builder)
static_analysis_builder.add_edge(START, "identify_suspicious_elements")
static_analysis_builder.add_edge("identify_suspicious_elements", "create_analysis_tasks")
static_analysis_builder.add_conditional_edges("create_analysis_tasks", assign_analysis_tasks, ["run_file_analysis", "review_analysis_results"])
static_analysis_builder.add_edge("run_file_analysis", "review_analysis_results")
static_analysis_builder.add_edge("summarize_file_analysis", END)

static_analysis_graph = static_analysis_builder.compile()
static_analysis_graph = static_analysis_graph.with_config(FILE_ANALYSIS_CONFIG)

if __name__ == "__main__":
    from .cli import main
    import asyncio
    
    asyncio.run(main())
