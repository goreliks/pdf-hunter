# Dev Mode Mock Data

This directory contains sample session logs for frontend development without running the backend analysis.

## Files

- **`mock-session.jsonl`** - Real session logs from a successful PDF analysis
  - Contains logs from all 5 agents (PDF Extraction, File Analysis, Image Analysis, URL Investigation, Report Generator)
  - Used when Dev Mode toggle is enabled on the landing page

## Usage

1. Toggle **Dev Mode** on the landing page
2. Dashboard will load and replay these logs instead of connecting to the backend
3. Perfect for:
   - Frontend UI development
   - Testing log visualization
   - Dashboard layout iteration
   - No need to run backend or wait for LLM responses

## How to Update Mock Data

After running a successful analysis in real mode:

```bash
cd frontend/dev

# Extract PdfExtraction logs from central log (they don't appear in session log)
grep '"session_id": "{YOUR_SESSION_ID}"' ../../logs/pdf_hunter_YYYYMMDD.jsonl | grep '"agent": "PdfExtraction"' > /tmp/pdf_logs.jsonl

# Get session logs and combine with PdfExtraction logs
cat /tmp/pdf_logs.jsonl ../../output/{session_id}/logs/session.jsonl > mock-session.jsonl

# Example for session ab7b10c590b66d7c3435d931c3dcada0f8ce9bff_20251002_000432:
grep '"session_id": "ab7b10c590b66d7c3435d931c3dcada0f8ce9bff_20251002_000432"' ../../logs/pdf_hunter_20251002.jsonl | grep '"agent": "PdfExtraction"' > /tmp/pdf_logs.jsonl
cat /tmp/pdf_logs.jsonl ../../output/ab7b10c590b66d7c3435d931c3dcada0f8ce9bff_20251002_000432/logs/session.jsonl > mock-session.jsonl
```

**Why combine logs?**  
PdfExtraction runs before session logging initializes, so its logs only appear in the central log file (`logs/pdf_hunter_YYYYMMDD.jsonl`), not in the session log. To get complete mock data with all 5 agents, we need to combine both sources.

## Note

Dev Mode automatically disables when:
- "New Analysis" button is clicked
- User manually toggles it off
- Page is refreshed (doesn't persist in sessionStorage)
