import asyncio
from contextlib import asynccontextmanager
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
_session_manager = None
_session_lock = None

def get_mcp_client():
    """Get or initialize MCP client lazily to avoid issues with LangGraph Platform."""
    global _client
    if _client is None:
        _client = MultiServerMCPClient(mcp_config)
    return _client

class MCPSessionManager:
    """Manages a persistent MCP session that can be reused across operations."""
    
    def __init__(self, client):
        self.client = client
        self.session_context = None
        self.session = None
        self._is_active = False
    
    async def get_session(self):
        """Get or create the active session."""
        if not self._is_active:
            await self._start_session()
        return self.session
    
    async def _start_session(self):
        """Start the session context."""
        if self._is_active:
            return
            
        self.session_context = self.client.session("playwright")
        self.session = await self.session_context.__aenter__()
        self._is_active = True
    
    async def cleanup(self):
        """Clean up the session context."""
        if self._is_active and self.session_context:
            try:
                await self.session_context.__aexit__(None, None, None)
            except Exception as e:
                print(f"Warning: Error during MCP session cleanup: {e}")
            finally:
                self._is_active = False
                self.session = None
                self.session_context = None

async def get_mcp_session():
    """Get or initialize a persistent MCP session for playwright.
    
    This function ensures a single session is maintained across all operations
    while being safe for concurrent access. The session is automatically 
    initialized when first accessed and reused for subsequent calls.
    """
    global _session_manager, _session_lock
    
    # Initialize the lock on first access
    if _session_lock is None:
        _session_lock = asyncio.Lock()
    
    async with _session_lock:
        if _session_manager is None:
            client = get_mcp_client()
            _session_manager = MCPSessionManager(client)
        
        return await _session_manager.get_session()

async def cleanup_mcp_session():
    """Cleanup the global MCP session. Call this when shutting down."""
    global _session_manager, _session_lock
    
    if _session_lock is None:
        return
        
    async with _session_lock:
        if _session_manager is not None:
            await _session_manager.cleanup()
            _session_manager = None