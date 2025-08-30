from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langgraph.prebuilt import ToolNode
from .schemas import InvestigatorState, InvestigatorOutputState, StaticAnalysisState, StaticAnalysisInputState
from .nodes import investigator_node, triage_router, update_mission_list, dispatch_investigations, reviewer_node, finalizer_node
from .tools import pdf_parser_tools
from langgraph.prebuilt import tools_condition



investigator_builder = StateGraph(InvestigatorState, output_schema=InvestigatorOutputState)

investigator_builder.add_node("investigation", investigator_node)
investigator_builder.add_node("tools", ToolNode(pdf_parser_tools))

investigator_builder.add_edge(START, "investigation")
investigator_builder.add_edge("tools", "investigation")

investigator_builder.add_conditional_edges(
    "investigation",
    tools_condition,  # This automatically routes to "tools" if tool_calls exist, otherwise continues
    {
        "tools": "tools",      # If tools_condition returns "tools"
        "__end__": END  # If tools_condition returns "__end__" (no tool calls)
    }
)

investigator_graph = investigator_builder.compile()


# Create a wrapper that ensures outputs are aggregated properly
def conduct_investigation(state: dict):
    """
    Wrapper for the investigator subgraph that ensures outputs are collected
    into the completed_investigations list.
    """
    # Run the investigator subgraph
    result = investigator_graph.invoke(state)
    
    # The result should contain the fields from InvestigatorOutputState
    # We need to wrap it in a list so it gets aggregated via operator.add
    return {
        "completed_investigations": [result]  # This will be aggregated
    }

# Add the wrapper as the node instead of the raw subgraph


static_analysis_builder = StateGraph(StaticAnalysisState, input_schema=StaticAnalysisInputState)

# Add nodes to static_analysis_builder
static_analysis_builder.add_node("triage", triage_router)
static_analysis_builder.add_node("update_mission_list", update_mission_list)
# static_analysis_builder.add_node("conduct_investigation", investigator_graph)
static_analysis_builder.add_node("conduct_investigation", conduct_investigation)
# static_analysis_builder.add_node("reducer_node", reducer_node)
static_analysis_builder.add_node("reviewer_node", reviewer_node)
static_analysis_builder.add_node("finalizer_node", finalizer_node)

# Add edges to static_analysis_builder (not investigator_builder)
static_analysis_builder.add_edge(START, "triage")
static_analysis_builder.add_edge("triage", "update_mission_list")
static_analysis_builder.add_conditional_edges("update_mission_list", dispatch_investigations, ["conduct_investigation", "reviewer_node"])
static_analysis_builder.add_edge("conduct_investigation", "reviewer_node")
static_analysis_builder.add_edge("finalizer_node", END)

static_analysis_graph = static_analysis_builder.compile()

if __name__ == "__main__":
    import json
    import os
    import uuid
    from datetime import datetime
    
    file_path = "/Users/gorelik/Courses/pdf-hunter/tests/87c740d2b7c22f9ccabbdef412443d166733d4d925da0e8d6e5b310ccfc89e13.pdf"
    output_directory="output"
    additional_context="None"
    session_id="123"

    final_state = None
    for event in static_analysis_graph.stream({"file_path":file_path,"output_directory": output_directory, "additional_context": additional_context, "session_id": session_id}, stream_mode="values"):
        print(event)
        final_state = event
    
    # Save final state to JSON file
    if final_state:
        # Generate unique filename with timestamp
        unique_id = uuid.uuid4().hex[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_report_session_{unique_id}_{timestamp}.json"
        
        # Ensure output directory exists
        os.makedirs(output_directory, exist_ok=True)
        
        # Full path for the JSON file
        json_path = os.path.join(output_directory, filename)
        
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
        
        # Save to JSON file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_state, f, indent=2, ensure_ascii=False)
        
        print(f"\n--- Final state saved to: {json_path} ---")
