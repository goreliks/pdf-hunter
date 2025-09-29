from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langgraph.prebuilt import ToolNode
from .schemas import InvestigatorState, InvestigatorOutputState, FileAnalysisState, FileAnalysisInputState, FileAnalysisOutputState
from .nodes import file_analyzer, identify_suspicious_elements, create_analysis_tasks, assign_analysis_tasks, review_analysis_results, summarize_file_analysis
from .tools import pdf_parser_tools
from langgraph.prebuilt import tools_condition
from pdf_hunter.shared.utils.logging_config import configure_logging, get_logger
from pdf_hunter.config import FILE_ANALYSIS_CONFIG, FILE_ANALYSIS_INVESTIGATOR_CONFIG

# Configure logging for this module
configure_logging()
logger = get_logger(__name__)



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
    mission = state.get("mission")
    if mission:
        logger.info(f"Starting investigation mission for threat type: {mission.threat_type}")
        logger.debug(f"Mission ID: {mission.mission_id}")
    
    # Run the investigator subgraph
    logger.debug("Invoking investigator subgraph")
    result = await investigator_graph.ainvoke(state)
    
    if result.get("investigation_report"):
        logger.info(f"Investigation completed: {result['investigation_report'].conclusion}")
    
    # The result should contain the fields from InvestigatorOutputState
    # We need to wrap it in a list so it gets aggregated via operator.add
    logger.debug("Returning mission result for aggregation")
    return {
        "completed_investigations": [result]  # This will be aggregated
    }

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
    import json
    import os
    import uuid
    import logging
    import asyncio
    from datetime import datetime
    
    # Configure more detailed logging for standalone execution
    configure_logging(level=logging.INFO, log_to_file=True)
    logger = get_logger(__name__)
    
    async def run_analysis():
        module_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(module_dir, "../../../.."))
        file_path = os.path.join(project_root, "tests", "assets", "pdfs", "87c740d2b7c22f9ccabbdef412443d166733d4d925da0e8d6e5b310ccfc89e13.pdf")
        
        output_directory = "output/file_analysis_results"
        additional_context = "None"
        session_id = "123"
    
        logger.info(f"Running file analysis on: {file_path}")
        logger.info(f"Session ID: {session_id}")
    
        final_state = None
        async for event in static_analysis_graph.astream({"file_path":file_path,"output_directory": output_directory, "additional_context": additional_context, "session_id": session_id}, stream_mode="values"):
            if logger.isEnabledFor(logging.DEBUG):
                # Don't log the full event as it can be very large
                event_keys = list(event.keys()) if isinstance(event, dict) else "Non-dict event"
                logger.debug(f"Event received with keys: {event_keys}")
            final_state = event
            
        # Save final state to JSON file if available
        if final_state:
            # Generate unique filename with timestamp
            unique_id = uuid.uuid4().hex[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_report_session_{unique_id}_{timestamp}.json"
            
            # Convert final state to JSON-serializable format
            def make_serializable(obj):
                if hasattr(obj, 'model_dump'):
                    return obj.model_dump()
                elif isinstance(obj, dict):
                    return {k: make_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [make_serializable(item) for item in obj]
                else:
                    return obj
            
            serializable_state = make_serializable(final_state)
            
            # Ensure output directory exists
            await asyncio.to_thread(os.makedirs, output_directory, exist_ok=True)
            
            # Full path for the JSON file
            json_path = os.path.join(output_directory, filename)
            
            # Save to JSON file
            logger.info(f"Saving final state to {json_path}")
            
            # Define the function to be run in a thread
            def write_json_file():
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(serializable_state, f, indent=2, ensure_ascii=False)
            
            # Run the file operation in a separate thread
            await asyncio.to_thread(write_json_file)
            logger.info(f"Final state saved to: {json_path}")
        
        return final_state
        
    # Run the async function
    asyncio.run(run_analysis())
