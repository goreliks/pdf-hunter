import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from langchain_mcp_adapters.client import MultiServerMCPClient

def get_mcp_config(task_id: str = None, base_output_dir: str = None):
    """Get MCP configuration with task-specific output directory under url_investigation."""
    # Default to current directory if no base directory provided
    if base_output_dir is None:
        base_output_dir = "./output"

    # Create url_investigation subdirectory under session directory
    url_investigation_dir = os.path.join(base_output_dir, "url_investigation")
    if task_id:
        task_output_dir = os.path.join(url_investigation_dir, f"task_{task_id}")
    else:
        task_output_dir = url_investigation_dir
        
    return {
        "playwright": {
            "command": "npx",
            "args": ["@playwright/mcp@latest", "--headless", f"--output-dir={task_output_dir}", "--save-trace", "--isolated"],
            "transport": "stdio"
        }
    }

_clients = {}
_session_managers = {}
_session_lock = None

def get_mcp_client(task_id: str = None, base_output_dir: str = None):
    """Get or initialize MCP client lazily to avoid issues with LangGraph Platform."""
    global _clients
    client_key = f"{task_id or 'default'}_{base_output_dir or 'default'}"
    if client_key not in _clients:
        _clients[client_key] = MultiServerMCPClient(get_mcp_config(task_id, base_output_dir))
    return _clients[client_key]

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

async def get_mcp_session(task_id: str = None, base_output_dir: str = None):
    """Get or initialize a task-specific MCP session for playwright.

    This function ensures isolated sessions for parallel tasks while being safe
    for concurrent access. Each task gets its own browser context and output directory.

    Args:
        task_id: Optional task identifier for session isolation. If None, uses default session.
        base_output_dir: Optional base output directory for session. If None, uses default.
    """
    global _session_managers, _session_lock

    # Initialize the lock on first access
    if _session_lock is None:
        _session_lock = asyncio.Lock()

    session_key = f"{task_id or 'default'}_{base_output_dir or 'default'}"

    async with _session_lock:
        if session_key not in _session_managers:
            client = get_mcp_client(task_id, base_output_dir)
            _session_managers[session_key] = MCPSessionManager(client)

        return await _session_managers[session_key].get_session()

async def cleanup_mcp_session(task_id: str = None):
    """Cleanup MCP session(s). Call this when shutting down.
    
    Args:
        task_id: If provided, cleanup only the specific task session. 
                 If None, cleanup all sessions.
    """
    global _session_managers, _session_lock
    
    if _session_lock is None:
        return
        
    async with _session_lock:
        if task_id:
            # Cleanup specific task session
            session_key = task_id
            if session_key in _session_managers:
                await _session_managers[session_key].cleanup()
                del _session_managers[session_key]
        else:
            # Cleanup all sessions
            for session_manager in _session_managers.values():
                await session_manager.cleanup()
            _session_managers.clear()
