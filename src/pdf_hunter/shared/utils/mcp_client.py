from langchain_mcp_adapters.client import MultiServerMCPClient
output_dir = "./mcp_outputs/final_pipeline_test"


mcp_config = {
            "playwright": {
                "command": "npx",
                "args": ["@playwright/mcp@latest", f"--output-dir={output_dir}", "--save-trace", "--isolated"],
                "transport": "stdio"
            }
        }

_client = None

def get_mcp_client():
    """Get or initialize MCP client lazily to avoid issues with LangGraph Platform."""
    global _client
    if _client is None:
        _client = MultiServerMCPClient(mcp_config)
    return _client