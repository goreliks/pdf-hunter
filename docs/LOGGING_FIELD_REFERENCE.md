# PDF Hunter Logging Field Reference

**Pure field mapping documentation for all agents and events.**  
This document contains only what exists in the logs - no examples, no integration code, just facts.

---

## Log Structure

Every log entry has this structure:
```
record.extra        ← All agent/event data here
record.level.name   ← Log severity (DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)
record.message      ← Human-readable text
record.time         ← Timestamp
```

---

## Core Fields (Present in Every Log)

| Field | Type | Description |
|-------|------|-------------|
| `agent` | string | Agent name (see Agent List below) |
| `node` | string | Current node/function name |
| `session_id` | string | Format: `{sha1}_{timestamp}` |
| `event_type` | string \| null | Specific event identifier (null for general logs) |

---

## Agent List

1. **PdfExtraction** - Extracts images and URLs from PDF
2. **FileAnalysis** - Analyzes file structure and creates investigation missions
3. **ImageAnalysis** (logs as `image_analysis`) - Analyzes page images for deception
4. **URLInvestigation** - Investigates embedded/QR URLs via browser automation
5. **ReportGenerator** - Synthesizes findings into final report

---

## Agent: PdfExtraction

### Node: setup_session
**Events:** `SESSION_CREATED`

| Event Type | Additional Fields | Field Types |
|------------|------------------|-------------|
| `SESSION_CREATED` | `session_id`, `output_directory` | string, string |

### Node: extract_pdf_images
**Events:** `IMAGE_EXTRACTION_START`, `IMAGE_EXTRACTION_COMPLETE`

| Event Type | Additional Fields | Field Types |
|------------|------------------|-------------|
| `IMAGE_EXTRACTION_START` | `file_path` | string |
| `IMAGE_EXTRACTION_COMPLETE` | `image_count`, `output_directory` | int, string |

### Node: find_embedded_urls
**Events:** `URL_SEARCH_START`, `URL_SEARCH_COMPLETE`

| Event Type | Additional Fields | Field Types |
|------------|------------------|-------------|
| `URL_SEARCH_START` | `file_path` | string |
| `URL_SEARCH_COMPLETE` | `url_count` | int |

### Node: scan_qr_codes
**Events:** `QR_SCAN_START`, `QR_SCAN_COMPLETE`

| Event Type | Additional Fields | Field Types |
|------------|------------------|-------------|
| `QR_SCAN_START` | `total_images` | int |
| `QR_SCAN_COMPLETE` | `qr_count`, `urls_decoded` | int, int |

---

## Agent: FileAnalysis

### Node: identify_suspicious_elements
**Events:** `TRIAGE_START`, `TRIAGE_COMPLETE`

| Event Type | Additional Fields | Field Types |
|------------|------------------|-------------|
| `TRIAGE_START` | `file_path` | string |
| `TRIAGE_COMPLETE` | `decision`, `mission_count`, `reasoning` | string, int, string |

**decision values:** `"innocent"`, `"suspicious"`, `"malicious"`

### Node: create_analysis_tasks
**Events:** `TASKS_CREATED`

| Event Type | Additional Fields | Field Types |
|------------|------------------|-------------|
| `TASKS_CREATED` | `task_count` | int |

### Node: assign_analysis_tasks
**Events:** `MISSION_ASSIGNED`, `NO_PENDING_MISSIONS`

| Event Type | Additional Fields | Field Types |
|------------|------------------|-------------|
| `MISSION_ASSIGNED` | `mission_id`, `mission_description` | string, string |
| `NO_PENDING_MISSIONS` | `total_missions`, `completed_missions` | int, int |

### Node: run_investigation
**Events:** `INVESTIGATION_START`, `INVESTIGATION_COMPLETE`, `INVESTIGATION_BLOCKED`

| Event Type | Additional Fields | Field Types |
|------------|------------------|-------------|
| `INVESTIGATION_START` | `mission_id` | string |
| `INVESTIGATION_COMPLETE` | `mission_id`, `mission_status` | string, string |
| `INVESTIGATION_BLOCKED` | `mission_id`, `reason` | string, string |

**mission_status values:** `"COMPLETED"`, `"FAILED"`, `"BLOCKED"`, `"NOT_RELEVANT"`

### Node: review_analysis_results
**Events:** `REVIEW_START`, `STRATEGIC_REVIEW_START`, `PROCESSING_COMPLETE`

| Event Type | Additional Fields | Field Types |
|------------|------------------|-------------|
| `REVIEW_START` | `completed_missions`, `failed_missions`, `blocked_missions` | int, int, int |
| `STRATEGIC_REVIEW_START` | (none) | |
| `PROCESSING_COMPLETE` | `reports_size`, `transcripts_size`, `graph_size` | int, int, int |

### Node: merge_findings
**Events:** `MERGE_COMPLETE`

| Event Type | Additional Fields | Field Types |
|------------|------------------|-------------|
| `MERGE_COMPLETE` | `total_findings` | int |

### Node: compile_file_analysis
**Events:** `ANALYSIS_COMPLETE`

| Event Type | Additional Fields | Field Types |
|------------|------------------|-------------|
| `ANALYSIS_COMPLETE` | `output_file` | string |

---

## Agent: ImageAnalysis (logs as `image_analysis`)

### Node: analyze_images
**Events:** `AGENT_START`, `PAGE_ANALYSIS_START`, `PAGE_ANALYSIS_COMPLETE`, `ANALYSIS_COMPLETE`

| Event Type | Additional Fields | Field Types |
|------------|------------------|-------------|
| `AGENT_START` | `pages_to_analyze` | int |
| `PAGE_ANALYSIS_START` | `page_number` | int |
| `PAGE_ANALYSIS_COMPLETE` | `page_number`, `findings_count`, `tactics_count`, `benign_count`, `urls_count` | int, int, int, int, int |
| `ANALYSIS_COMPLETE` | `pages_analyzed` | int |

### Node: compile_findings
**Events:** `COMPILATION_START`, `VERDICT_DETERMINED`, `COMPILATION_COMPLETE`

| Event Type | Additional Fields | Field Types |
|------------|------------------|-------------|
| `COMPILATION_START` | `total_findings`, `total_tactics`, `total_benign`, `total_urls` | int, int, int, int |
| `VERDICT_DETERMINED` | `verdict`, `confidence` | string, float |
| `COMPILATION_COMPLETE` | `final_verdict`, `final_confidence`, `priority_urls_count` | string, float, int |

**verdict values:** `"Benign"`, `"Suspicious"`, `"Malicious"`  
**confidence range:** 0.0 to 1.0

---

## Agent: URLInvestigation

### Node: filter_urls
**Events:** `FILTER_START`, `FILTER_COMPLETE`

| Event Type | Additional Fields | Field Types |
|------------|------------------|-------------|
| `FILTER_START` | `total_urls` | int |
| `FILTER_COMPLETE` | `urls_to_investigate`, `urls_skipped` | int, int |

### Node: setup_url_investigation
**Events:** `SETUP_COMPLETE`

| Event Type | Additional Fields | Field Types |
|------------|------------------|-------------|
| `SETUP_COMPLETE` | `mission_directory` | string |

### Node: investigate_url
**Events:** `INVESTIGATION_START`, `TOOL_EXECUTION_COMPLETE`, `ANALYSIS_COMPLETE`

| Event Type | Additional Fields | Field Types |
|------------|------------------|-------------|
| `INVESTIGATION_START` | `url`, `priority` | string, int |
| `TOOL_EXECUTION_COMPLETE` | `url`, `tool_count` | string, int |
| `ANALYSIS_COMPLETE` | `url`, `verdict`, `confidence`, `mission_status` | string, string, float, string |

**verdict values:** `"Benign"`, `"Suspicious"`, `"Malicious"`, `"Inaccessible"`  
**mission_status values:** `"COMPLETED"`, `"FAILED"`

### Node: compile_url_findings
**Events:** `COMPILATION_START`, `COMPILATION_COMPLETE`

| Event Type | Additional Fields | Field Types |
|------------|------------------|-------------|
| `COMPILATION_START` | `investigation_count` | int |
| `COMPILATION_COMPLETE` | `verdict`, `confidence` | string, float |

### Node: save_results
**Events:** `SAVE_COMPLETE`

| Event Type | Additional Fields | Field Types |
|------------|------------------|-------------|
| `SAVE_COMPLETE` | `investigation_count`, `output_file` | int, string |

---

## Agent: ReportGenerator

### Node: determine_threat_verdict
**Events:** `VERDICT_DETERMINATION_START`, `VERDICT_DETERMINED`

| Event Type | Additional Fields | Field Types |
|------------|------------------|-------------|
| `VERDICT_DETERMINATION_START` | (none) | |
| `VERDICT_DETERMINED` | `verdict`, `confidence`, `reasoning_preview`, `full_reasoning` | string, float, string (100 chars), string (full text) |

**verdict values:** `"Benign"`, `"Suspicious"`, `"Malicious"`

### Node: generate_final_report
**Events:** `REPORT_GENERATION_START`, `REPORT_GENERATION_COMPLETE`

| Event Type | Additional Fields | Field Types |
|------------|------------------|-------------|
| `REPORT_GENERATION_START` | (none) | |
| `REPORT_GENERATION_COMPLETE` | `report_length`, `report_preview`, `markdown_report` | int, string (200 chars), string (full markdown) |

### Node: save_analysis_results
**Events:** `SAVE_START`, `ANALYSIS_COMPLETE`

| Event Type | Additional Fields | Field Types |
|------------|------------------|-------------|
| `SAVE_START` | (none) | |
| `ANALYSIS_COMPLETE` | `session_id`, `report_path`, `final_verdict`, `final_confidence` | string, string, string, float |

---

## System Events

These appear outside normal agent flows:

### Agent: system

| Node | Event Type | Additional Fields |
|------|------------|------------------|
| `setup_logging` | (null) | `debug_to_terminal`, `session_id` |
| `unknown` | (null) | (varies) |

### Agent: orchestrator

| Node | Event Type | Additional Fields |
|------|------------|------------------|
| `unknown` | (null) | (varies) |

---

## Log Levels

| Level | Numeric Value | Usage |
|-------|--------------|-------|
| `DEBUG` | 10 | Detailed diagnostic information |
| `INFO` | 20 | General operational events |
| `SUCCESS` | 25 | Successful completion events |
| `WARNING` | 30 | Warning conditions |
| `ERROR` | 40 | Error events |
| `CRITICAL` | 50 | Critical system failures |

---

## Special Field Details

### session_id Format
- Pattern: `{sha1_hash}_{timestamp}`
- Example: `ab7b10c590b66d7c3435d931c3dcada0f8ce9bff_20251001_121946`
- SHA1: First 40 characters (PDF file hash)
- Timestamp: Format `YYYYMMDD_HHMMSS`

### Verdict Values
All agents that determine verdicts use these three values:
- `"Benign"` - No threat detected
- `"Suspicious"` - Potential threat, needs review
- `"Malicious"` - Confirmed threat

URL investigation adds:
- `"Inaccessible"` - URL could not be reached

### Mission Status Values
Used by FileAnalysis and URLInvestigation:
- `"COMPLETED"` - Mission finished successfully
- `"FAILED"` - Mission encountered errors
- `"BLOCKED"` - Mission hit recursion/complexity limit
- `"NOT_RELEVANT"` - Mission determined to be unnecessary

### Decision Values (FileAnalysis triage)
- `"innocent"` - No suspicious indicators found
- `"suspicious"` - Some concerning patterns detected
- `"malicious"` - High-confidence threat indicators present

---

## Complex Object Fields

Some events include nested objects. These are serialized as JSON strings in the logs.

### DetailedFinding (ImageAnalysis)
Fields: `issue`, `location`, `severity`, `evidence`, `page_number`

### DeceptionTactic (ImageAnalysis)
Fields: `tactic_name`, `description`, `risk_level`, `page_number`

### BenignSignal (ImageAnalysis)
Fields: `signal`, `explanation`, `page_number`

### PrioritizedURL (ImageAnalysis, URLInvestigation)
Fields: `url`, `priority`, `context`, `source_page`

### AnalystFindings (ImageAnalysis final output)
Fields: `detailed_findings`, `deception_tactics`, `benign_signals`, `overall_verdict`, `confidence_score`, `prioritized_urls`

### URLAnalysisResult (URLInvestigation)
Fields: `url`, `verdict`, `confidence`, `findings`, `tool_executions`, `final_analysis`

### FinalVerdict (ReportGenerator)
Fields: `verdict`, `confidence`, `key_findings`, `reasoning`
