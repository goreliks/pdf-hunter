from langgraph.graph import StateGraph, START, END
from .nodes import generate_final_report, determine_threat_verdict, save_analysis_results
from pdf_hunter.config import REPORT_GENERATION_CONFIG

# The finalizer's state is the same as the Orchestrator's, so no need to redefine
from ...orchestrator.schemas import OrchestratorState

# We can use a simple builder here as the state is passed directly from the orchestrator
report_generator_builder = StateGraph(OrchestratorState)

report_generator_builder.add_node("generate_final_report", generate_final_report)
report_generator_builder.add_node("determine_threat_verdict", determine_threat_verdict)
report_generator_builder.add_node("save_analysis_results", save_analysis_results)

report_generator_builder.add_edge(START, "determine_threat_verdict")
report_generator_builder.add_edge("determine_threat_verdict", "generate_final_report")
report_generator_builder.add_edge("generate_final_report", "save_analysis_results")
report_generator_builder.add_edge("save_analysis_results", END)

report_generator_graph = report_generator_builder.compile()
report_generator_graph = report_generator_graph.with_config(REPORT_GENERATION_CONFIG)

if __name__ == "__main__":
    import json
    import pprint
    import os
    import asyncio
    import glob
    from loguru import logger
    from pdf_hunter.config.logging_config import setup_logging
    
    # Configure logging with more verbose output for standalone execution with DEBUG output
    setup_logging(debug_to_terminal=True)
    
    async def run_report_generator():
        # Directly use a known file path in the output directory
        test_json_path = "/Users/gorelik/Courses/pdf-hunter/output/242fc6a46e4b36fcc00a3cfaabefe29a8cf8a5c9_20250929_170003/file_analysis/file_analysis_state_session_242fc6a46e4b36fcc00a3cfaabefe29a8cf8a5c9_20250929_170003.json"
        
        # Check if the specific file exists
        if not os.path.exists(test_json_path):
            logger.warning(f"Specified file not found: {test_json_path}", agent="TestRunner", node="load_state")
            
            # Try to find any session directory with JSON files as a fallback
            output_dir = "/Users/gorelik/Courses/pdf-hunter/output"
            logger.info(f"Looking for any analysis files in: {output_dir}", agent="TestRunner", node="load_state")
            
            # Find all JSON files in the output directory (recursively)
            all_json_files = glob.glob(f"{output_dir}/**/*.json", recursive=True)
            
            if not all_json_files:
                logger.warning("No JSON files found in output directory", agent="TestRunner", node="search_files")
                
                # Create a minimal test state
                test_state = {
                    "file_path": "/path/to/test.pdf",
                    "session_id": "test_session_id",
                    "output_directory": "output/test_session",
                    "file_analysis_report": {
                        "verdict": "suspicious",
                        "findings": ["Sample test finding for report generator"],
                        "evidence_graph": {"nodes": [], "edges": []}
                    },
                    "image_analysis_report": {
                        "page_verdicts": [{"page": 0, "verdict": "benign", "confidence": 0.9}],
                        "all_priority_urls": []
                    },
                    "url_investigation_results": []
                }
                return test_state
                
            # Sort by modification time (most recent first)
            all_json_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            test_json_path = all_json_files[0]
        
        logger.info(f"Using JSON file: {test_json_path}", agent="TestRunner", node="load_state")
        
        try:
            with open(test_json_path, 'r', encoding='utf-8') as f:
                test_state = json.load(f)
            
            logger.info(f"🚀 Running Report Generator on test state from: {test_json_path}", agent="TestRunner", node="run_graph")
            # Use ainvoke instead of invoke
            final_state = await report_generator_graph.ainvoke(test_state)
            
            logger.success("✅ Report Generator Complete", agent="TestRunner", node="run_graph")
            return final_state
        except FileNotFoundError:
            logger.error(f"File not found: {test_json_path}", agent="TestRunner", node="run_graph")
            return None
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in file: {test_json_path}", agent="TestRunner", node="run_graph")
            return None
        except Exception as e:
            logger.error(f"Error running report generator: {str(e)}", agent="TestRunner", node="run_graph", exc_info=True)
            return None
    
    # Run the async function
    final_state = asyncio.run(run_report_generator())
    
    # Verify the results
    if final_state:
        print("\n--- Verification ---")
        if final_state.get("errors"):
            logger.warning(f"Completed with {len(final_state['errors'])} error(s).", agent="TestRunner", node="verify")
        else:
            logger.success("✅ Completed successfully.", agent="TestRunner", node="verify")
            logger.info(f"Final Report Generated: {'Yes' if final_state.get('final_report') else 'No'}", agent="TestRunner", node="verify")
            logger.info(f"Final Verdict Generated: {'Yes' if final_state.get('final_verdict') else 'No'}", agent="TestRunner", node="verify")
            if final_state.get('final_verdict'):
                logger.info("Final Verdict Details:", agent="TestRunner", node="verify")
                pprint.pprint(final_state['final_verdict'].model_dump_json(indent=2))
