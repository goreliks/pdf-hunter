from langchain.tools import tool
from langchain_core.tools import InjectedToolArg
import subprocess
import json
import os
import re
import hashlib
import binascii
import tempfile
import shlex
from typing import Optional, Annotated
import sys
from importlib.resources import files


def _run_command(command: str) -> str:
    """A centralized, safe function to run shell commands and return structured output."""
    try:
        # Use shlex.split for security to prevent shell injection vulnerabilities.
        # It correctly handles arguments with spaces if they are quoted.
        command_parts = shlex.split(command)
        process = subprocess.run(
            command_parts,
            capture_output=True,
            text=True,
            timeout=30,  # Prevent long-running commands
            check=True   # Raise an exception if the command returns a non-zero exit code
        )
        # Return stdout if successful. Stderr is captured in the exception.
        return process.stdout.strip()
    except FileNotFoundError:
        return f"Error: The command '{command_parts[0]}' was not found. It may not be installed or in the system's PATH."
    except subprocess.CalledProcessError as e:
        # This catches errors from the command itself (e.g., file not found for 'cat')
        return f"Error executing command. Return code: {e.returncode}\nStderr: {e.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"An unexpected error occurred: {e}"

@tool
def view_file_as_hex(file_path: str) -> str:
    """
    CRITICAL DIAGNOSTIC TOOL. Views the full hexadecimal and ASCII representation of any file.
    Use this when 'view_file_strings' yields no or unhelpful output to analyze the raw file
    structure, identify file headers, or find embedded binary data.
    """
    return _run_command(f"xxd {file_path}")

@tool
def identify_file_type(file_path: str) -> str:
    """
    Identifies the type of a file (e.g., 'ASCII text', 'PE32 executable', 'Zip archive data').
    This is a crucial first step after dumping any stream to disk to understand what kind of
    artifact you are dealing with.
    """
    return _run_command(f"file {file_path}")

@tool
def analyze_rtf_objects(file_path: str) -> str:
    """
    Analyze RTF files for embedded objects and OLE packages using rtfobj from oletools.
    This is a READ-ONLY analysis tool that identifies malicious objects in RTF files.
    
    CRITICAL: Use this tool ONCE after extracting any file identified as 
    'Rich Text Format' by identify_file_type. 
    
    What this tool DOES:
    - Identifies embedded OLE objects and their class names (e.g., EqUatiON.3)
    - Shows data sizes and MD5 hashes
    - Flags known exploit indicators (e.g., CVE-2017-11882)
    
    What this tool CANNOT DO:
    - Extract or save the OLE payload to disk (not supported by rtfobj)
    - Provide more details than shown in the output
    - Return different results if called multiple times on the same file
    
    IMPORTANT: Once you see the exploit indicator (e.g., "Equation Editor vulnerability"),
    you have ALL the information available. DO NOT call this tool again on the same file.
    Write your MissionReport with the CVE, MD5 hash, and class name provided.
    """
    return _run_command(f"rtfobj {file_path}")

@tool
def search_file_for_pattern(pattern: str, file_path: str) -> str:
    """
    Searches for a specific keyword or pattern within any file, treating it as text.
    Essential for finding suspicious indicators like URLs, IP addresses, or function names
    (e.g., 'eval', 'CreateObject') inside dumped scripts or binary files.
    """
    # Using -a to treat binary files as text and -i for case-insensitivity
    return _run_command(f"grep -a -i '{pattern}' {file_path}")

@tool
def view_full_text_file(file_path: str) -> str:
    """
    Displays the complete, raw content of a text file. Use this ONLY when the
    'identify_file_type' tool has confirmed the file is a script or text-based,
    as it can produce garbled output for binary files.
    """
    return _run_command(f"cat {file_path}")

@tool
def list_directory_contents(directory_path: str) -> str:
    """
    Lists all files and their details (permissions, size, modification date) in the
    specified directory. Use '.' for the current working/output directory. Useful
    for confirming that a file dump was successful and for getting the names of
    artifacts to analyze.
    """
    return _run_command(f"ls -l {directory_path}")

# =========================
# Internal helpers
# =========================

def _make_env_with_objstm(enabled: bool) -> dict:
    """
    Return an env mapping with PDFPARSER_OPTIONS ensuring -O is present/absent.
    We keep it additive and idempotent.
    """
    env = os.environ.copy()
    opts = env.get("PDFPARSER_OPTIONS", "").split()
    if enabled:
        if "-O" not in opts and "--objstm" not in opts:
            opts.append("-O")
    else:
        # drop -O/--objstm if present
        opts = [o for o in opts if o not in ("-O", "--objstm")]
    env["PDFPARSER_OPTIONS"] = " ".join(opts).strip()
    return env


def run_pdf_parser(pdf_file_path: str, options=None, use_objstm: bool = True, timeout: Optional[int] = 120):
    """
    Internal function to run pdf-parser.py with given options.

    - Statelessness: Each call launches a fresh process. Nothing is persisted between calls.
    - ObjStm resolution: We enable -O by default via PDFPARSER_OPTIONS so inner objects are visible in THIS call.
      Pass use_objstm=False to opt out (e.g., for very large files when speed matters).

    Args:
        pdf_file_path: absolute path to the PDF file
        options: list of CLI flags/args to append (e.g., ["--stats"])
        use_objstm: include -O on this invocation (default True)
        timeout: subprocess timeout in seconds

    Returns:
        str: combined stdout + stderr
    """
    pdf_parser_path = str(files("pdf_hunter.shared.analyzers.external") / "pdf-parser.py")
    
    # Verify the file exists
    if not os.path.exists(pdf_parser_path):
        raise FileNotFoundError(f"pdf-parser.py not found at {pdf_parser_path}")

    if options is None:
        options = []
    if isinstance(options, dict):
        options = []

    # ensure -O really gets used when requested
    opts = list(options)
    if use_objstm and not any(o in ("-O", "--objectstreams") for o in opts):
        opts = ["-O"] + opts

    command = [sys.executable, pdf_parser_path] + opts + [pdf_file_path]

    try:
        # Use the current directory since we have an absolute path to pdf-parser.py
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            env=_make_env_with_objstm(use_objstm),
            timeout=timeout,
        )

        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            # make stderr visible but separate
            output += f"\nErrors/Warnings:\n{result.stderr}"

        if result.returncode != 0 and not output:
            output = f"Command failed with return code {result.returncode}"

        return output if output else "No output generated"

    except Exception as e:
        return f"Error running pdf-parser: {str(e)}"


def _looks_like_filtered_stream_needed(text: str) -> bool:
    """
    Heuristic to determine whether we should re-run with --filter:
    - Output mentions 'Contains stream' AND a /Filter key, but no filtered bytes shown yet.
    - IMPORTANT: Skip auto-filter if stream is too large (> 100KB compressed)
    """
    has_stream = "Contains stream" in text
    has_filter_key = "/Filter" in text
    
    if not (has_stream and has_filter_key):
        return False
    
    # Check stream size to avoid decompressing huge files
    # Look for /Length in the output (e.g., "/Length 2004304")
    length_match = re.search(r'/Length\s+(\d+)', text)
    if length_match:
        stream_size = int(length_match.group(1))
        MAX_AUTO_FILTER_SIZE = 100000  # 100KB compressed - reasonable limit
        if stream_size > MAX_AUTO_FILTER_SIZE:
            # Don't auto-filter large streams - agent should use dump_object_stream instead
            return False
    
    return True


def _safe_preview_bytes(b: bytes, max_len: int = 256) -> str:
    """
    Return a short Base64 preview for logging without spewing raw bytes.
    """
    try:
        import base64
        return base64.b64encode(b[:max_len]).decode()
    except Exception:
        return ""


def _write_bytes(path: str, data: bytes) -> str:
    try:
        with open(path, "wb") as f:
            f.write(data)
        return f"[WRITE] {len(data)} bytes → {path}"
    except Exception as e:
        return f"[ERROR] writing to {path}: {e}"


def _mostly_printable_ascii(data: bytes, threshold: float = 0.85) -> bool:
    """
    Return True if data is mostly printable ASCII (plus tab/newline/carriage return).
    """
    if not data:
        return False
    printable = set(range(32, 127)) | {9, 10, 13}  # ASCII + \t \n \r
    good = sum(1 for b in data if b in printable)
    ratio = good / max(1, len(data))
    return ratio >= threshold


def _bytes_to_safe_text(data: bytes, max_chars: int = 2000) -> str:
    """
    Decode bytes to a readable string for logging. We try UTF-8 then fall back to latin-1.
    """
    try:
        s = data.decode("utf-8", errors="replace")
    except Exception:
        s = data.decode("latin-1", errors="replace")
    if len(s) > max_chars:
        s = s[:max_chars] + "\n[truncated]"
    return s


def _extract_strings_from_bytes(
    data: bytes,
    min_len: int = 4,
    utf16: bool = True,
    limit: int = 10000,
) -> str:
    """
    Same logic as strings() but operates on an in-memory byte buffer.
    """
    # ASCII strings
    asc = re.findall(rb"[ -~]{%d,}" % min_len, data)
    out_lines = [s.decode(errors="ignore") for s in asc]

    if utf16:
        try:
            u16 = re.findall(rb"(?:[ -~]\x00){%d,}" % min_len, data)
            out_lines.extend([s.decode("utf-16le", errors="ignore") for s in u16])
        except Exception:
            pass

    if not out_lines:
        return "(no strings found)"
    if len(out_lines) > limit:
        out_lines = out_lines[:limit] + ["[truncated]"]
    return "\n".join(out_lines)


_OBJSTM_PTRN = re.compile(r"Containing /ObjStm:\s*(\d+)\s+0")

def _extract_objstm_id(text: str) -> Optional[int]:
    m = _OBJSTM_PTRN.search(text)
    return int(m.group(1)) if m else None


def _is_mostly_printable(b: bytes, min_ratio: float = 0.85, max_nuls: float = 0.02) -> bool:
    if not b:
        return False
    nuls = b.count(0) / len(b)
    ok = set(range(32,127)) | {9,10,13}  # printable + \t\r\n
    printable = sum(1 for x in b if x in ok) / len(b)
    return printable >= min_ratio and nuls <= max_nuls


def _decode_text(b: bytes) -> str:
    # try UTF-8 then fall back
    try:
        return b.decode("utf-8", errors="strict")
    except Exception:
        return b.decode("latin-1", errors="replace")


def _write_temp(prefix: str, data: bytes, suffix: str = ".bin", output_dir: Optional[str] = None) -> str:
    """Write bytes to a temp file. If output_dir is provided, use it; otherwise use system temp."""
    if output_dir:
        # Create file_analysis subdirectory within output_dir
        target_dir = os.path.join(output_dir, "file_analysis")
        os.makedirs(target_dir, exist_ok=True)
    else:
        target_dir = "/tmp"
    with tempfile.NamedTemporaryFile(prefix=prefix, suffix=suffix, delete=False, dir=target_dir) as f:
        f.write(data)
        return f.name

# =========================
# Core pdf-parser wrappers
# =========================

@tool
def get_pdf_stats(
    use_objstm: bool = True,
    pdf_file_path: Annotated[str, InjectedToolArg] = None
) -> str:
    """
    Display statistics about the PDF (counts per object type, unreferenced objects, suspicious keywords, etc).

    IMPORTANT: Stateless. Each call is a fresh process. ObjStm resolution (-O) is enabled by default so that
    inner objects that live inside /ObjStm are included in THIS call's statistics.
    Disable with use_objstm=False if you explicitly don't want to synthesize objects from streams.

    Args:
        use_objstm: Enable ObjStm resolution (default: True)
        pdf_file_path: Absolute path to the PDF (injected at runtime)

    Returns:
        Raw string output of pdf-parser --stats (with -O enabled by default).
    """
    return run_pdf_parser(pdf_file_path, options=["--stats"], use_objstm=use_objstm)


@tool
def search_pdf_content(
    search_string: str,
    case_sensitive: bool = False,
    regex: bool = False,
    in_streams: bool = False,
    use_objstm: bool = True,
    filtered_streams: bool = True,
    pdf_file_path: Annotated[str, InjectedToolArg] = None
) -> str:
    """
    Search for a string/regex in objects or streams (ideal for IOCs: /JavaScript, /OpenAction, /Launch, etc).

    Statelessness & ObjStm:
    - Every call is a new process; there is NO persistence.
    - ObjStm resolution (-O) is enabled by default, so searching can find hits inside /ObjStm.
    - For stream searches, `filtered_streams=True` searches decompressed content (adds --filter); set False to search raw.

    Args:
        search_string: String or regex to search for.
        case_sensitive: Case-sensitive search in streams (default False).
        regex: Treat search_string as regex (default False).
        in_streams: True to search streams (--searchstream), False to search in objects (--search).
        use_objstm: Include -O for this call (default True).
        filtered_streams: When in_streams=True, search filtered (decompressed) data (default True).
        pdf_file_path: Absolute path to the PDF (injected at runtime)

    Returns:
        Raw output listing matching objects/streams.
    """
    options = []
    if in_streams:
        options.extend(["--searchstream", search_string])
        if filtered_streams:
            options.append("--filter")
    else:
        options.extend(["--search", search_string])

    if case_sensitive:
        options.append("--casesensitive")
    if regex:
        options.append("--regex")

    return run_pdf_parser(pdf_file_path, options=options, use_objstm=use_objstm)


@tool
def dump_object_stream(
    object_id: int,
    dump_file_path: str,
    filter_stream: bool = False,
    use_objstm: bool = True,
    pdf_file_path: Annotated[str, InjectedToolArg] = None
) -> str:
    """
    Dump the content of a specific object's STREAM to a file for further analysis.

    - If the object has a stream and `filter_stream=True`, the stream is decompressed via --filter (Flate, ASCIIHex, ASCII85, LZW, RLE).
    - Stateless. ObjStm (-O) is enabled by default so you can dump streams that live inside /ObjStm containers.

    Args:
        object_id: Object number to dump.
        dump_file_path: Destination path for the dumped bytes.
        filter_stream: Decompress before dumping.
        use_objstm: Include -O on this call (default True).
        pdf_file_path: Absolute path to the PDF file (injected at runtime)

    Returns:
        pdf-parser output + write confirmation/error.
    """
    options = ["--object", str(object_id), "--dump", dump_file_path]
    if filter_stream:
        options.append("--filter")
    return run_pdf_parser(pdf_file_path, options=options, use_objstm=use_objstm)


@tool
def parse_objstm(
    object_id: int,
    filtered: bool = True,
    use_objstm: bool = True,
    pdf_file_path: Annotated[str, InjectedToolArg] = None
) -> str:
    """
    Parse a specific /ObjStm container by its ID and (optionally) print the DECOMPRESSED body.

    WHY: If a target object yields no output, it's often embedded inside an /ObjStm. Parsing the container with
    filtering reveals the inner objects (mirrors CLI: `-o <id> -O -f`).

    Statelessness & ObjStm:
    - Each call is fresh. Resolution of object streams does not persist.
    - -O is enabled by default on this call. Disable with use_objstm=False.

    Args:
        object_id: The ID of the /ObjStm container (NOT an inner object).
        filtered: When True (default), pass --filter to show the decompressed stream body.
        use_objstm: Include -O on this call (default True).
        pdf_file_path: Absolute path to the PDF (injected at runtime)

    Returns:
        Raw output showing the /ObjStm dictionary and, if filtered=True, the decompressed concatenation of inner objects.
    """
    options = ["--objstm", "--object", str(object_id)]
    if filtered:
        options.append("--filter")
    return run_pdf_parser(pdf_file_path, options=options, use_objstm=use_objstm)


@tool
def get_object_content(
    object_id: int,
    filter_stream: bool = False,
    use_objstm: bool = True,
    pdf_file_path: Annotated[str, InjectedToolArg] = None
) -> str:
    """
    Retrieve an object by ID; auto-runs --filter for SMALL streams (< 100KB compressed).
    Stateless. -O is injected by default so inner objects are visible.
    
    IMPORTANT: For large streams (> 100KB), this tool shows METADATA only. 
    If you need the actual content of a large stream, use dump_object_stream with 
    the output_file parameter to save it to disk instead.
    
    Args:
        object_id: Object number to retrieve.
        filter_stream: Decompress stream content (default False).
        use_objstm: Include -O on this call (default True).
        pdf_file_path: Absolute path to the PDF (injected at runtime)
    """
    base_opts = ["--object", str(object_id)]
    
    # First, get metadata without filtering to check stream size
    out = run_pdf_parser(pdf_file_path, options=base_opts, use_objstm=use_objstm)
    
    # Check stream size BEFORE filtering (even if explicitly requested)
    if "Contains stream" in out and "/Filter" in out:
        length_match = re.search(r'/Length\s+(\d+)', out)
        if length_match:
            stream_size = int(length_match.group(1))
            MAX_FILTER_SIZE = 100000  # 100KB compressed
            if stream_size > MAX_FILTER_SIZE and filter_stream:
                # Refuse to filter large streams even if explicitly requested
                out += f"\n\n[ERROR: Stream is {stream_size:,} bytes compressed (> 100KB). Cannot filter - would exceed context limits.]"
                out += f"\n[Use dump_object_stream with output_file parameter to save it to disk instead.]"
                filter_stream = False  # Override the request
    
    # Now apply filtering only if approved
    if filter_stream:
        out = run_pdf_parser(pdf_file_path, options=base_opts + ["--filter"], use_objstm=use_objstm)

    # Check if we should auto-filter this stream (skips large streams automatically)
    if (not filter_stream) and _looks_like_filtered_stream_needed(out):
        out2 = run_pdf_parser(pdf_file_path, options=["--object", str(object_id), "--filter"], use_objstm=use_objstm)
        out = f"{out}\n\n[auto --filter re-run]\n{out2}"
    elif (not filter_stream) and "Contains stream" in out and "/Filter" in out:
        # Large stream was skipped - add helpful message
        length_match = re.search(r'/Length\s+(\d+)', out)
        if length_match:
            stream_size = int(length_match.group(1))
            if stream_size > 100000:
                out += f"\n\n[NOTE: Stream is {stream_size:,} bytes compressed (> 100KB). Auto-filter skipped to prevent context overflow.]"
                out += f"\n[To analyze this stream, use dump_object_stream with output_file parameter to save it to disk.]"

    objstm_id = _extract_objstm_id(out)
    if objstm_id is not None:
        auto = run_pdf_parser(pdf_file_path, options=["--object", str(objstm_id), "--filter"], use_objstm=use_objstm)
        out = f"{out}\n\n[auto --object {objstm_id} --filter]\n{auto}"

    return out


@tool
def get_objects_by_type(
    object_type: str,
    use_objstm: bool = True,
    pdf_file_path: Annotated[str, InjectedToolArg] = None
) -> str:
    """
    List all objects of a given /Type (e.g., '/JavaScript', '/Launch', '/XObject', '/Annot').

    Stateless & ObjStm:
    - Fresh process every time; no persistence.
    - -O is enabled by default so objects living inside /ObjStm are included.

    Args:
        object_type: The name (e.g., '/JavaScript', '/Launch').
        use_objstm: Include -O on this call (default True).
        pdf_file_path: Absolute path to the PDF file (injected at runtime)

    Returns:
        Raw output listing objects of the specified type.
    """
    options = ["--type", object_type]
    return run_pdf_parser(pdf_file_path, options=options, use_objstm=use_objstm)


@tool
def get_object_stream_only(
    object_id: int,
    filtered: bool = True,
    base64_output: bool = True,
    output_file: Optional[str] = None,
    use_objstm: bool = True,
    pdf_file_path: Annotated[str, InjectedToolArg] = None
) -> str:
    """
    Return ONLY the stream bytes of an object (ideal for /ObjStm dumps), optionally as Base64.

    Implementation detail:
    - Uses `--object <id> --jsonoutput` (and `--filter` if filtered=True). The parser returns a JSON with base64-encoded
      stream content for objects that have a stream. We extract the first item.

    Args:
        object_id: Object number.
        filtered: Decompress via --filter (default True).
        base64_output: When True, return a JSON string with {"b64": "..."}; otherwise return a short diagnostic string.
        output_file: If provided, write raw bytes to this path.
        use_objstm: Include -O on this call (default True).
        pdf_file_path: Absolute path to the PDF (injected at runtime)

    Returns:
        JSON string with fields:
          {"b64": "<base64>", "meta": {"rc": 0, "stderr": ""}}
        Or a human-readable message when base64_output=False.
    """
    options = ["--object", str(object_id), "--jsonoutput"]
    if filtered:
        options.append("--filter")

    raw = run_pdf_parser(pdf_file_path, options=options, use_objstm=use_objstm)
    # Separate stderr if appended
    if "Errors/Warnings:" in raw:
        stdout, _, stderr = raw.partition("Errors/Warnings:")
        err = stderr.strip()
    else:
        stdout = raw
        err = ""

    try:
        data = json.loads(stdout.strip())
        items = data.get("items", [])
        if not items:
            resp = {"b64": "", "meta": {"rc": 1, "stderr": "No stream found for this object"}}
            return json.dumps(resp)
        # Take the first stream
        b64 = items[0].get("content", "")
        blob = binascii.a2b_base64(b64) if b64 else b""

        wrote = ""
        if output_file:
            wrote = _write_bytes(output_file, blob)

        if base64_output:
            return json.dumps({"b64": b64, "meta": {"rc": 0, "stderr": err}})
        else:
            return f"[OK] {len(blob)} bytes extracted. {wrote or ''}".strip()

    except Exception as e:
        resp = {"b64": "", "meta": {"rc": 2, "stderr": f"json parse error or no stream: {e}"}}
        return json.dumps(resp)


# =========================
# Analyst niceties (helpers)
# =========================

@tool
def b64_decode(
    input_string: Optional[str] = None,
    input_file: Optional[str] = None,
    output_file: Optional[str] = None,
    urlsafe: bool = False,
    strict: bool = False,
    text_mode: bool = True,
    make_temp_file: bool = False,
    strings_on_output: bool = False,
    strings_min_len: int = 4,
    strings_utf16: bool = True,
    output_directory: Annotated[Optional[str], InjectedToolArg] = None
) -> str:
    """
    Base64-decode a string or file.
    - text_mode=True: if decoded bytes are mostly printable, return plaintext.
    - make_temp_file=True: write decoded bytes to output_directory (or /tmp if not specified).
    - strings_on_output=True: run strings on the decoded BYTES ONLY (never on the PDF).
    
    Args:
        input_string: Base64 string to decode (mutually exclusive with input_file)
        input_file: File containing base64 data (mutually exclusive with input_string)
        output_file: Specific output file path
        urlsafe: Use URL-safe Base64 variant
        strict: Strict validation mode
        text_mode: Return as text if mostly printable (default True)
        make_temp_file: Create temp file in output_directory
        strings_on_output: Extract strings from decoded bytes
        strings_min_len: Minimum string length for extraction (default 4)
        strings_utf16: Include UTF-16 strings (default True)
        output_directory: Target directory for temp files (injected at runtime)
    """
    import base64
    try:
        if input_string is not None:
            data = input_string.encode()
        elif input_file:
            with open(input_file, "rb") as f:
                data = f.read()
        else:
            return "Provide input_string or input_file."

        decoded = base64.b64decode(data, altchars=b"-_", validate=strict) if urlsafe \
                  else base64.b64decode(data, validate=strict)

        wrote = ""
        if output_file:
            wrote = _write_bytes(output_file, decoded)
        elif make_temp_file:
            tmp = _write_temp("decoded_b64_", decoded, output_dir=output_directory)
            wrote = f"[WRITE] {len(decoded)} bytes → {tmp}"

        if text_mode and _is_mostly_printable(decoded):
            text = _decode_text(decoded)
            return (f"[OK] Decoded {len(decoded)} bytes. {wrote}\n[TEXT]\n{text}").strip()

        parts = [f"[OK] Decoded {len(decoded)} bytes."]
        if wrote:
            parts.append(wrote)

        if strings_on_output:
            parts.append("[STRINGS from decoded bytes]")
            parts.append(_extract_strings_from_bytes(decoded, min_len=strings_min_len, utf16=strings_utf16))

        parts.append(f"[PREVIEW b64] {_safe_preview_bytes(decoded)}")
        return "\n".join(parts).strip()

    except Exception as e:
        return f"[ERROR] b64_decode: {e}"


@tool
def hex_decode(
    hex_string: Optional[str] = None,
    input_file: Optional[str] = None,
    output_file: Optional[str] = None,
    ignore_whitespace: bool = True,
    # New behavior toggles:
    prefer_text: bool = True,
    text_threshold: float = 0.85,
    max_plaintext_chars: int = 2000,
    strings_on_output: bool = False,
    strings_min_len: int = 4,
    strings_utf16: bool = True,
    output_directory: Annotated[Optional[str], InjectedToolArg] = None
) -> str:
    """
    Decode hex-encoded data (e.g., PDF <...> payloads or hex strings).

    New:
    - prefer_text=True: if decoded bytes are "mostly printable", return PLAINTEXT instead of a base64 preview.
      Tunable via text_threshold and max_plaintext_chars.
    - strings_on_output=True: run strings on the decoded BYTES ONLY (not the whole PDF). Writes a temp file to
      output_directory (or system temp if not specified) and includes its path for follow-up tooling.

    Args:
        hex_string: Hex string to decode (mutually exclusive with input_file)
        input_file: File containing hex data (mutually exclusive with hex_string)
        output_file: Specific output file path
        ignore_whitespace: Strip whitespace before decoding (default True)
        prefer_text: Return plaintext if mostly printable (default True)
        text_threshold: Printability threshold for text mode (default 0.85)
        max_plaintext_chars: Max characters to return in text mode (default 2000)
        strings_on_output: Extract strings from decoded bytes
        strings_min_len: Minimum string length for extraction (default 4)
        strings_utf16: Include UTF-16 strings (default True)
        output_directory: Target directory for temp files (injected at runtime)

    Returns a PLAINTEXT block when applicable or a short Base64 preview; optionally writes bytes to output_file.
    """
    try:
        if hex_string is None and input_file is None:
            return "Provide hex_string or input_file."

        if input_file:
            with open(input_file, "rb") as f:
                s = f.read().decode(errors="ignore")
        else:
            s = hex_string

        # Strip angle brackets if a PDF-like <....> was pasted
        s = s.strip()
        if s.startswith("<") and s.endswith(">"):
            s = s[1:-1]

        if ignore_whitespace:
            s = re.sub(r"\s+", "", s)

        data = binascii.unhexlify(s)

        wrote_lines = []
        if output_file:
            wrote_lines.append(_write_bytes(output_file, data))

        temp_path = None
        strings_block = None
        if strings_on_output:
            # Create file_analysis subdirectory if output_directory is provided
            if output_directory:
                target_dir = os.path.join(output_directory, "file_analysis")
                os.makedirs(target_dir, exist_ok=True)
            else:
                target_dir = None
            fd, temp_path = tempfile.mkstemp(prefix="decoded_", suffix=".bin", dir=target_dir)
            os.close(fd)
            wrote_lines.append(_write_bytes(temp_path, data))
            strings_block = _extract_strings_from_bytes(data, min_len=strings_min_len, utf16=strings_utf16)

        # Prefer plaintext when it's likely human-readable
        if prefer_text and _mostly_printable_ascii(data, threshold=text_threshold):
            text = _bytes_to_safe_text(data, max_chars=max_plaintext_chars)
            parts = [f"[OK] Decoded {len(data)} bytes.", *wrote_lines, "[PLAINTEXT]", text]
        else:
            preview_b64 = _safe_preview_bytes(data)
            parts = [f"[OK] Decoded {len(data)} bytes.", *wrote_lines, f"[PREVIEW b64] {preview_b64}"]

        if strings_on_output:
            parts.append("\n[STRINGS from decoded bytes]")
            parts.append(strings_block or "(no strings found)")
            if temp_path:
                parts.append(f"[TEMP FILE] {temp_path}")

        return "\n".join(p for p in parts if p).strip()

    except Exception as e:
        return f"[ERROR] hex_decode: {e}"


@tool
def hexdump(input_file: str, max_bytes: int = 4096, width: int = 16, offset: int = 0) -> str:
    """
    Produce a simple hex+ASCII dump of a file segment.

    Args:
        input_file: Path to file.
        max_bytes: Number of bytes to dump.
        width: Bytes per line.
        offset: Start offset in file.

    Returns:
        A printable hexdump string.
    """
    try:
        with open(input_file, "rb") as f:
            if offset:
                f.seek(offset)
            data = f.read(max_bytes)

        lines = []
        for i in range(0, len(data), width):
            chunk = data[i : i + width]
            hexpart = " ".join(f"{b:02X}" for b in chunk)
            asciipart = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            lines.append(f"{offset+i:08X}: {hexpart:<{width*3}} {asciipart}")
        return "\n".join(lines) if lines else "(no data)"

    except Exception as e:
        return f"[ERROR] hexdump: {e}"


@tool
def strings(input_file: str, min_len: int = 4, utf16: bool = True, max_bytes: int = 1_000_000) -> str:
    """
    Extract printable strings from a file segment (ASCII and optionally UTF-16LE).

    Args:
        input_file: Path to file.
        min_len: Minimum length of a string to include.
        utf16: Also extract UTF-16LE strings (default True).
        max_bytes: Cap how much to read (default 1MB to avoid huge output).

    Returns:
        Newline-delimited strings (truncated to avoid runaway output).
    """
    try:
        with open(input_file, "rb") as f:
            data = f.read(max_bytes)

        # ASCII
        asc = re.findall(rb"[ -~]{%d,}" % min_len, data)
        out_lines = [s.decode(errors="ignore") for s in asc]

        # UTF-16LE
        if utf16:
            try:
                u16 = re.findall(rb"(?:[ -~]\x00){%d,}" % min_len, data)
                out_lines.extend([s.decode("utf-16le", errors="ignore") for s in u16])
            except Exception:
                pass

        # Limit output size
        if len(out_lines) > 10_000:
            out_lines = out_lines[:10_000] + ["[truncated]"]

        return "\n".join(out_lines) if out_lines else "(no strings found)"

    except Exception as e:
        return f"[ERROR] strings: {e}"


@tool
def grep_file(input_file: str, pattern: str, regex: bool = True, ignore_case: bool = True, max_bytes: int = 1_000_000) -> str:
    """
    Grep-like search in a file (useful for dumped streams or artifacts).

    Args:
        input_file: Path to file.
        pattern: String or regex.
        regex: Treat pattern as regex (default True). If False, a plain substring match is used.
        ignore_case: Case-insensitive when regex=True (default True).
        max_bytes: Cap how much to read.

    Returns:
        Matching lines (best-effort line splitting on \\n).
    """
    try:
        with open(input_file, "rb") as f:
            data = f.read(max_bytes)
        text = data.decode(errors="ignore")
        lines = text.splitlines()

        if regex:
            flags = re.IGNORECASE if ignore_case else 0
            r = re.compile(pattern, flags)
            matches = [ln for ln in lines if r.search(ln)]
        else:
            needle = pattern.lower() if ignore_case else pattern
            matches = [ln for ln in lines if (needle in ln.lower())] if ignore_case else [ln for ln in lines if (needle in ln)]

        if not matches:
            return "(no matches)"
        # cap output
        if len(matches) > 5000:
            matches = matches[:5000] + ["[truncated]"]
        return "\n".join(matches)

    except Exception as e:
        return f"[ERROR] grep_file: {e}"


@tool
def file_info(input_file: str, hash_algos: str = "md5,sha1,sha256", max_bytes: int = 4096) -> str:
    """
    Lightweight file info: size, a few hashes, and a quick magic sniff (very basic; no external deps).

    Args:
        input_file: Path to file.
        hash_algos: Comma-separated list (e.g., 'md5,sha1,sha256').
        max_bytes: Bytes to read for magic sniff and for hashing chunked read size.

    Returns:
        Multi-line string with size, hashes, and a naive magic guess.
    """
    try:
        size = os.path.getsize(input_file)
        algos = [a.strip().lower() for a in hash_algos.split(",") if a.strip()]
        h = {}
        for a in algos:
            if a not in hashlib.algorithms_available and a not in ("md5", "sha1", "sha256"):
                continue
            h[a] = hashlib.new(a)

        with open(input_file, "rb") as f:
            head = f.read(max_bytes)
            # hash whole file in chunks
            for algo in h.values():
                algo.update(head)
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                for algo in h.values():
                    algo.update(chunk)

        # naive magic sniff
        magic = "unknown"
        if head.startswith(b"%PDF-"):
            magic = "PDF document"
        elif head.startswith(b"\x1F\x8B\x08"):
            magic = "GZIP compressed"
        elif head.startswith(b"PK\x03\x04"):
            magic = "ZIP container / OOXML"
        elif head.startswith(b"\x89PNG\r\n\x1A\n"):
            magic = "PNG image"

        lines = [f"Path: {input_file}", f"Size: {size} bytes", f"Type: {magic}"]
        for name, algo in h.items():
            lines.append(f"{name.upper()}: {algo.hexdigest()}")
        return "\n".join(lines)

    except Exception as e:
        return f"[ERROR] file_info: {e}"


@tool
def get_xmp_metadata(
    pdf_file_path: Annotated[str, InjectedToolArg] = None
) -> str:
    """
    Extract XMP metadata from PDF for document provenance analysis.

    XMP metadata reveals document creation history:
    - Creator tool (e.g., "PDFescape Online - https://www.pdfescape.com")
    - Producer tool (e.g., "RAD PDF 3.15.0.0 - https://www.radpdf.com")
    - Creation and modification timestamps
    - Document ID and version information

    Use this to detect suspicious patterns:
    - Multiple online editors used (possible evasion tactic)
    - Rapid tool switching (< 1 minute between modifications)
    - Unusual tool combinations (obfuscation)
    - Automated malware generation indicators

    Returns:
        XMP XML content with creator, producer, timestamps, and tool chain information
    """
    try:
        # First, search for /Metadata object to get its ID
        search_result = run_pdf_parser(pdf_file_path, options=["-s", "/Metadata"], use_objstm=True)

        if "obj" not in search_result.lower():
            return "[INFO] No XMP metadata object found in PDF (no /Metadata objects)"

        # Extract metadata object ID from Referencing line (e.g., "Referencing: 6 0 R, 9 0 R")
        # The /Metadata reference is typically the second reference in /Catalog
        ref_match = re.search(r'Referencing:.*?(\d+)\s+0\s+R,\s+(\d+)\s+0\s+R', search_result)
        if ref_match:
            # Try the second reference first (usually /Metadata)
            metadata_obj_id = int(ref_match.group(2))
        else:
            # Fallback: look for "obj X 0" pattern (but this might match the Catalog)
            obj_match = re.search(r'obj\s+(\d+)\s+\d+', search_result)
            if not obj_match:
                return "[INFO] Could not parse /Metadata object ID from search results"
            metadata_obj_id = int(obj_match.group(1))

        # Get the metadata object stream content (--content dumps the stream)
        metadata_content = run_pdf_parser(
            pdf_file_path,
            options=["--object", str(metadata_obj_id), "--content"],
            use_objstm=True
        )

        if not metadata_content or len(metadata_content) < 50:
            return f"[INFO] Metadata object {metadata_obj_id} found but contains no XMP data"

        # Extract the XML portion (starts with <?xpacket and ends with <?xpacket end)
        xml_start = metadata_content.find("<?xpacket")
        xml_end = metadata_content.find("<?xpacket end")

        if xml_start == -1:
            # No XML found, return raw content
            return f"[INFO] Metadata object {metadata_obj_id} content (not XML format):\n{metadata_content}"

        if xml_end != -1:
            xml_end = metadata_content.find("?>", xml_end) + 2
            xmp_xml = metadata_content[xml_start:xml_end]
        else:
            xmp_xml = metadata_content[xml_start:]

        # Parse key provenance fields for easy reading
        provenance_info = []

        # Extract Creator
        creator_match = re.search(r'<xmp:CreatorTool>(.+?)</xmp:CreatorTool>', xmp_xml, re.DOTALL)
        if creator_match:
            provenance_info.append(f"Creator Tool: {creator_match.group(1).strip()}")

        # Extract Producer
        producer_match = re.search(r'<pdf:Producer>(.+?)</pdf:Producer>', xmp_xml, re.DOTALL)
        if producer_match:
            provenance_info.append(f"Producer: {producer_match.group(1).strip()}")

        # Extract Creation Date
        create_date_match = re.search(r'<xmp:CreateDate>(.+?)</xmp:CreateDate>', xmp_xml, re.DOTALL)
        if create_date_match:
            provenance_info.append(f"Created: {create_date_match.group(1).strip()}")

        # Extract Modification Date
        mod_date_match = re.search(r'<xmp:ModifyDate>(.+?)</xmp:ModifyDate>', xmp_xml, re.DOTALL)
        if mod_date_match:
            provenance_info.append(f"Modified: {mod_date_match.group(1).strip()}")

        # Extract DynaPDF toolkit info (from xmptk attribute)
        toolkit_match = re.search(r'x:xmptk="(.+?)"', xmp_xml)
        if toolkit_match:
            provenance_info.append(f"XMP Toolkit: {toolkit_match.group(1).strip()}")

        # Build the output
        result_parts = []
        result_parts.append(f"=== XMP Metadata from Object {metadata_obj_id} ===\n")

        if provenance_info:
            result_parts.append("Document Provenance:")
            for info in provenance_info:
                result_parts.append(f"  • {info}")
            result_parts.append("")

        result_parts.append("Full XMP XML:")
        result_parts.append(xmp_xml)

        return "\n".join(result_parts)

    except Exception as e:
        return f"[ERROR] get_xmp_metadata: {e}"


# =========================
# Tool registry & manifest
# =========================

pdf_parser_tools = [
    get_pdf_stats,
    search_pdf_content,
    dump_object_stream,
    parse_objstm,
    get_object_content,
    get_objects_by_type,
    get_object_stream_only,
    get_xmp_metadata,  # NEW: Document provenance analysis
    # niceties
    b64_decode,
    hex_decode,
    hexdump,
    strings,
    grep_file,
    file_info,
    view_file_as_hex,
    identify_file_type,
    analyze_rtf_objects,
    search_file_for_pattern,
    view_full_text_file,
    list_directory_contents,
]

pdf_parser_tools_manifest = {tool.name: tool.description for tool in pdf_parser_tools}

if __name__ == "__main__":
    # Test the pdf-parser path resolution
    # try:
    #     test_pdf = str(Path(__file__).resolve().parent.parent.parent.parent / "tests" / "87c740d2b7c22f9ccabbdef412443d166733d4d925da0e8d6e5b310ccfc89e13.pdf")
    #     print(f"Testing with PDF: {test_pdf}")
    #     result = run_pdf_parser(test_pdf, options=["--stats"])
    #     print(result)
    # except Exception as e:
    #     print(f"Error: {e}")


    # run ls -l
    print(list_directory_contents("."))