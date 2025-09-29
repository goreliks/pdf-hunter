import os
import sys
import subprocess
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
from functools import lru_cache
from importlib.resources import files, as_file


@lru_cache
def get_pdfid_path() -> str:
    with as_file(files("pdf_hunter.shared.analyzers.external") / "pdfid.py") as p:
        return str(p)


@lru_cache
def get_pdf_parser_path() -> str:
    with as_file(files("pdf_hunter.shared.analyzers.external") / "pdf-parser.py") as p:
        return str(p)


async def _run_shell_command(command: List[str]) -> Dict[str, Any]:
    """A centralized, safe function to run shell commands and return structured output."""
    try:
        # Use asyncio.to_thread to avoid blocking the event loop
        def run_cmd(cmd):
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
                encoding='utf-8',
                errors='ignore' # Ignore errors for weird binary output
            )
        
        process = await asyncio.to_thread(run_cmd, command)
        return {
            "stdout": process.stdout.strip(),
            "stderr": process.stderr.strip(),
            "return_code": process.returncode
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "ERROR: Command timed out.", "return_code": -1}
    except FileNotFoundError:
        return {"stdout": "", "stderr": f"ERROR: Executable '{command[0]}' not found.", "return_code": -1}
    except Exception as e:
        return {"stdout": "", "stderr": f"ERROR: An unexpected error occurred: {e}", "return_code": -1}




async def run_pdfid(pdf_filename: str) -> str:
    """Runs the pdfid.py tool with the correct flags."""
    # Use pathlib for more reliable path handling
    pdfid_path = get_pdfid_path()
    
    if not os.path.exists(pdfid_path):
        print(f"Warning: pdfid.py not found at {pdfid_path}. Using simulation.")
        raise FileNotFoundError(f"pdfid.py not found at {pdfid_path}")
        #         return "/OpenAction -> /oPENaCTION\n..."


    command_parts = [sys.executable, pdfid_path, "-e", "-f", pdf_filename]
    result = await _run_shell_command(command_parts)
    return result['stdout'] or f"Tool executed with no output. Stderr: {result['stderr']}"


async def run_pdf_parser_full_statistical_analysis(pdf_filename: str) -> str:
    """Runs the pdf-parser.py tool with -a flag."""
    # Use pathlib for more reliable path handling
    pdf_parser_path = get_pdf_parser_path()
    
    if not os.path.exists(pdf_parser_path):
        print(f"Warning: pdf-parser.py not found at {pdf_parser_path}. Using simulation.")
        raise FileNotFoundError(f"pdf-parser.py not found at {pdf_parser_path}")

    command_parts = [sys.executable, pdf_parser_path, "-a", "-O", pdf_filename]
    result = await _run_shell_command(command_parts)
    return result['stdout'] or f"Tool executed with no output. Stderr: {result['stderr']}"


async def run_peepdf(pdf_filename: str) -> str:
    """Runs the peepdf.py tool with the correct flags."""
    command_parts = ["peepdf", "-f", pdf_filename]
    result = await _run_shell_command(command_parts)
    return result['stdout'] or f"Tool executed with no output. Stderr: {result['stderr']}"




if __name__ == "__main__":
    import asyncio

    async def main():
        test_pdf = "test.pdf"
        if os.path.exists(test_pdf):
            print(await run_pdfid(test_pdf))
            print(await run_pdf_parser_full_statistical_analysis(test_pdf))
            print(await run_peepdf(test_pdf))
        else:
            print(f"Test file {test_pdf} not found.")
    
    asyncio.run(main())