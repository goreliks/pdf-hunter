# Image Analysis Agent - Technical Documentation

## Overview

The **Image Analysis Agent** is the **third agent** in the pdf-hunter multi-agent pipeline and serves as the **Visual Deception Analyst (VDA)**. It performs sophisticated visual forensic analysis of rendered PDF pages, cross-referencing visual elements with technical metadata to detect deception tactics, phishing attempts, and brand impersonation.

**Position in Pipeline**: 

```
PDF Extraction
    ├→ File Analysis ──────────────┐
    └→ IMAGE ANALYSIS → URL Investigation ──┤
                                            ├→ Report Generator → END
                                            ┘
```

The Image Analysis agent runs in parallel with File Analysis (both receive PDF Extraction output), then feeds its prioritized URLs directly to the URL Investigation agent.

**Core Purpose**: Analyze the visual layer of PDF pages using multimodal AI to identify visual deception tactics, assess document trustworthiness, and prioritize suspicious URLs for deeper investigation.

## Core Principles & Philosophical Framework

The Image Analysis agent operates under a foundational philosophical framework that distinguishes it from traditional phishing detection approaches. This framework guides every aspect of the agent's design, from prompt engineering to verdict determination.

### The Three Core Principles

**1. "Autonomy is Disease"**
- **Meaning**: Any capability for automatic or autonomous action in a PDF is inherently suspicious and warrants immediate investigation.
- **Implementation**: While this principle is primarily enforced by the File Analysis agent (which investigates /OpenAction, /JavaScript, /Launch), the Image Analysis agent extends it to the visual layer: automated redirects, hidden links, and interface elements that attempt to bypass user decision-making are treated as high-priority threats.
- **Rationale**: Legitimate documents present information and wait for user action; malicious documents attempt to act autonomously to bypass user scrutiny.

**2. "Deception is Confession"**
- **Meaning**: Any form of visual or structural inconsistency is treated as evidence of malicious intent rather than incompetence.
- **Implementation**: The agent actively hunts for mismatches between visual presentation and technical reality (e.g., Microsoft logo with non-Microsoft URL, urgent language with sketchy domain). These inconsistencies are weighted heavily in verdict determination.
- **Rationale**: Attackers must deceive to succeed; legitimate organizations maintain visual-technical coherence. When deception is detected, it confesses malicious intent.

**3. "Incoherence is a Symptom"**
- **Meaning**: Cross-modal and cross-page inconsistencies are high-signal indicators of malicious documents.
- **Implementation**: The agent performs cross-modal analysis (visual + technical metadata) and cross-page analysis (comparing branding/narrative across pages) to detect incoherence. Even subtle inconsistencies elevate suspicion.
- **Rationale**: Legitimate documents maintain coherent narratives and consistent design; malicious documents often cobble together stolen assets, creating detectable incoherence.

### The Impartial Judge Requirement

**Critical Design Constraint**: The agent must function as an **impartial judge**, actively searching for evidence of **legitimacy (coherence)** with the same diligence it hunts for evidence of **deception (incoherence)**.

**Why This Matters**:
- **False Positive Reduction**: Without balanced analysis, aggressive design (legitimate marketing) triggers false positives.
- **Explainability**: Verdicts must weigh both sides, providing reasoned decisions rather than pattern matching.
- **Adversarial Robustness**: Attackers can't simply "look benign" - they must maintain coherence across all dimensions.

**Implementation**: The two-sided analytical framework (Part A: Hunting Incoherence, Part B: Searching Coherence) embedded in the system prompt enforces this requirement at the LLM reasoning level.

### How Principles Guide System Design

These principles directly inform key design decisions:

1. **Sequential Page Analysis**: Enables cross-page coherence checking ("incoherence is a symptom")
2. **Cross-Modal Integration**: Visual evidence + technical metadata reveals deception ("deception is confession")
3. **Verdict Logic**: Most severe page wins because any deception invalidates legitimacy ("deception is confession")
4. **Structured Prompts**: Two-sided framework implements "impartial judge" requirement
5. **URL Prioritization**: Visual context determines which autonomy attempts warrant investigation ("autonomy is disease")

**Research Contribution**: This philosophical framework represents a shift from pattern-matching detection to principle-based forensic analysis, enabling generalization across attack types without retraining.

## Architecture

### Graph Structure

The agent uses **LangGraph** with a simple two-stage sequential workflow:

```
START
  ↓
analyze_pdf_images
  ↓
compile_image_findings
  ↓
END
```

**Implementation**: `src/pdf_hunter/agents/image_analysis/graph.py`

### State Management

**State Schema**: `ImageAnalysisState` (TypedDict)

**Inputs from PDF Extraction**:
- `session_id` (str): Unique session identifier for output organization
- `output_directory` (str): Base output directory for session artifacts
- `extracted_images` (List[ExtractedImage]): Base64-encoded page images with metadata
- `extracted_urls` (List[ExtractedURL]): URLs extracted from PDF with coordinates
- `number_of_pages_to_process` (int): Maximum number of pages to analyze

**Internal State**:
- `page_analyses` (List[PageAnalysisResult]): Per-page analysis results
- `errors` (Annotated[List[str], operator.add]): Accumulated error messages

**Outputs**:
- `visual_analysis_report` (ImageAnalysisReport): Comprehensive final report
- `prioritized_urls` (List[PrioritizedURL]): URLs flagged for URL Investigation agent

**Implementation**: `src/pdf_hunter/agents/image_analysis/schemas.py`

## Core Nodes

### 1. analyze_pdf_images

**Purpose**: Perform page-by-page visual forensic analysis using multimodal LLM with cross-page context awareness.

**Process Flow**:

1. **Input Validation & Preparation**:
   - Validates presence of extracted images
   - Filters images based on `number_of_pages_to_process` limit
   - Sorts images by page number for sequential analysis
   - Groups URLs by page number for cross-modal correlation

2. **Sequential Page Analysis Loop**:
   For each page (in order):
   
   a. **Context Preparation**:
      - Creates "Element Map" containing all interactive elements (URLs) for current page
      - Includes previous page's analysis as forensic context (cross-page coherence checking)
      - First page receives: "This is the first page. There is no prior context."
   
   b. **LLM Invocation**:
      - Constructs multimodal message with:
        * System prompt: Visual Deception Analyst persona
        * User prompt: Formatted with element map and previous page context
        * Image data: Base64-encoded PNG of current page
      - Uses structured output binding to `PageAnalysisResult` schema
      - Timeout protection: 120 seconds (configurable via `LLM_TIMEOUT_VISION`)
   
   c. **Result Processing**:
      - Extracts structured analysis: findings, tactics, signals, verdict
      - Logs comprehensive metrics for monitoring
      - Generates "forensic briefing" for next page's context

3. **Cross-Page Context Generation**:
   - Helper function: `_create_structured_forensic_briefing()`
   - Filters for high-significance findings only
   - Extracts URLs from technical data for context
   - Creates concise briefing for next page's analysis

**Key Features**:
- **Timeout Protection**: Prevents infinite hangs on vision API calls
- **Comprehensive Logging**: INFO, WARNING levels for different finding types
- **Cross-Page Awareness**: Each page sees high-confidence findings from previous pages
- **Structured Output**: Pydantic schema enforcement ensures consistent data structure

**Logging Events**:
- `AGENT_START`: Analysis initiation
- `PAGE_ANALYSIS_START`: Beginning of each page
- `PAGE_ANALYSIS_COMPLETE`: Page verdict and metrics
- `HIGH_SIGNIFICANCE_FINDING`: Critical findings (WARNING level)
- `DECEPTION_TACTICS_DETECTED`: Identified manipulation techniques (WARNING level)
- `BENIGN_SIGNALS_DETECTED`: Legitimacy indicators
- `URLS_PRIORITIZED`: URLs flagged for investigation
- `ANALYSIS_COMPLETE`: All pages processed
- `ERROR`: Failures and timeouts

**Implementation**: `src/pdf_hunter/agents/image_analysis/nodes.py::analyze_pdf_images()`

### 2. compile_image_findings

**Purpose**: Aggregate all page-level analyses into a comprehensive final report with overall verdict.

**Aggregation Process**:

1. **Input Validation**:
   - Checks for available page analyses
   - Handles empty case with safe default report

2. **Document Flow Summary Generation**:
   - Sorts pages by page number
   - Creates sequential narrative: "Page N: [description]"
   - Provides document structure overview

3. **Overall Verdict Determination**:
   - **Verdict Logic**: Most severe page verdict becomes overall verdict
   - **Severity Ranking**: Benign (0) < Suspicious (1) < Highly Deceptive (2)
   - **Confidence Calculation**: Maximum confidence among pages with highest threat level
   - **Rationale**: "Weakest link" security principle aligned with "deception is confession" - any page exhibiting deception invalidates the entire document's trustworthiness, as legitimate documents maintain coherence across all pages

4. **Finding Aggregation**:
   - Flattens all page-level findings into unified lists:
     * `all_detailed_findings`: Cross-modal forensic findings
     * `all_deception_tactics`: Identified manipulation techniques
     * `all_benign_signals`: Legitimacy indicators
     * `all_priority_urls`: URLs for investigation (with status tracking)

5. **Executive Summary Generation**:
   - Synthesizes: page count, verdict, confidence, finding counts
   - Provides high-level assessment suitable for non-technical stakeholders

6. **Report Persistence**:
   - Creates `image_analysis/` subdirectory in session output
   - Saves complete report as JSON: `image_analysis_state_session_{session_id}.json`
   - Uses safe serialization for Pydantic models

**Logging Events**:
- `COMPILATION_START`: Report generation begins
- `VERDICT_DETERMINED`: Overall verdict with full metrics
- `REPORT_SAVED`: File path confirmation
- `COMPILATION_COMPLETE`: Success summary
- `ERROR`: Compilation failures

**Implementation**: `src/pdf_hunter/agents/image_analysis/nodes.py::compile_image_findings()`

## Key Data Structures

### PageAnalysisResult
```python
class PageAnalysisResult(BaseModel):
    page_description: str           # Objective appearance summary
    detailed_findings: List[DetailedFinding]  # Cross-modal forensics
    deception_tactics: List[DeceptionTactic]  # Manipulation techniques
    benign_signals: List[BenignSignal]        # Legitimacy indicators
    prioritized_urls: List[PrioritizedURL]    # URLs for investigation
    visual_verdict: Literal["Benign", "Suspicious", "Highly Deceptive"]
    confidence_score: float         # 0.0-1.0
    summary: str                    # Concise explanation
```

### DetailedFinding
```python
class DetailedFinding(BaseModel):
    element_type: str               # link, button, logo, etc.
    page_number: int                # 0-indexed page location
    visual_description: str         # What it looks like
    technical_data: Optional[str]   # JSON string: {"url": "...", "xref": ...}
    assessment: str                 # Analysis of the finding
    significance: Literal["low", "medium", "high"]
```

### DeceptionTactic
```python
class DeceptionTactic(BaseModel):
    tactic_type: str                # Type of manipulation
    description: str                # Detailed explanation
    confidence: float               # 0.0-1.0
    evidence: List[str]             # Supporting evidence list
```

### BenignSignal
```python
class BenignSignal(BaseModel):
    signal_type: str                # Type of legitimacy indicator
    description: str                # Detailed explanation
    confidence: float               # 0.0-1.0
```

### PrioritizedURL
```python
class PrioritizedURL(BaseModel):
    url: str                        # The URL requiring analysis
    priority: int                   # 1=highest, 5=lowest
    reason: str                     # Why flagged
    page_number: int                # Where found (0-indexed)
    source_context: Optional[str]   # Document context
    extraction_method: Optional[str] # qr_code, annotation, text
    mission_status: URLMissionStatus # NEW, IN_PROGRESS, COMPLETED, etc.
```

### ImageAnalysisReport
```python
class ImageAnalysisReport(BaseModel):
    overall_verdict: Literal["Benign", "Suspicious", "Highly Deceptive"]
    overall_confidence: float
    executive_summary: str
    document_flow_summary: str      # Sequential page descriptions
    page_analyses: List[PageAnalysisResult]
    all_detailed_findings: List[DetailedFinding]
    all_deception_tactics: List[DeceptionTactic]
    all_benign_signals: List[BenignSignal]
    all_priority_urls: List[PrioritizedURL]
```

## Prompt Engineering Strategy

### Critical Importance of Prompt Design

The Image Analysis agent's effectiveness fundamentally depends on **carefully engineered prompts** that translate the core philosophical principles into actionable LLM reasoning patterns. This prompt engineering is a **core research contribution** that enables principle-based detection without retraining.

**Why Prompt Engineering Matters Here**:
1. **Principle Implementation**: Prompts operationalize abstract principles ("deception is confession") into concrete analytical questions
2. **False Positive Reduction**: Balanced prompts implement "impartial judge" requirement, reducing over-flagging
3. **Systematic Reasoning**: Structured questions guide LLM through comprehensive cross-examination aligned with "incoherence is a symptom"
4. **Multi-Modal Integration**: Prompts explicitly instruct cross-referencing visual + technical data (detecting deception)
5. **Explainability**: Framework produces detailed reasoning showing how principles were applied
6. **Consistency**: Structured output binding ensures reliable downstream processing

### System Prompt: Visual Deception Analyst (VDA)

**Persona Engineering**: Synthesis of three complementary expert roles:
1. **HCI & UI/UX Security Specialist**: Analyzes dark patterns, visual deception, interface manipulation
2. **Cognitive Psychologist**: Identifies social engineering tactics, emotional manipulation, urgency triggers
3. **Digital Forensics Analyst**: Performs technical cross-examination, evidence correlation

**Rationale**: Each perspective detects different threat classes that map to the core principles:
- HCI catches design deception and psychological manipulation ("deception is confession")
- Psychology catches emotional levers that bypass rational thought ("autonomy is disease")
- Forensics catches cross-modal inconsistencies ("incoherence is a symptom")

**Core Philosophy Embedded in Prompt**:
The system prompt explicitly states the three principles and the "impartial judge" requirement, ensuring the LLM's reasoning aligns with the foundational framework:

```
"Your core philosophy is this: autonomy is disease, deception is confession, 
and incoherence is a symptom. Your mission is to judge a document's 
trustworthiness by assessing its holistic integrity. You must be an impartial 
judge, actively searching for evidence of legitimacy (coherence) with the 
same diligence that you hunt for evidence of deception (incoherence)."
```

**The Two-Sided Analytical Framework**:

This framework is the **key innovation** preventing false positives:

**Part A: Hunting for Incoherence (Signs of Deception)**
1. **Identity & Brand Impersonation**: 
   - Question: Is there contradiction between visual brand and technical URLs?
   - Example: Microsoft logo + suspicious non-Microsoft domain
   - Cross-page check: Does branding contradict previous pages?

2. **Psychological Manipulation**: 
   - Question: Does design use Urgency, Fear, or Authority to bypass rational thought?
   - Example: "Your account will be closed in 24 hours!" with countdown timer
   - Dark patterns: Making malicious path most prominent

3. **Interactive Element Deception**: 
   - Question: Does link text match actual destination?
   - Example: "Click here to verify" → leads to phishing site
   - OS/app mimicry: Fake system dialogs as hyperlinked images

4. **Structural Deception**: 
   - Question: Does structure contradict appearance?
   - Example: Appears scanned (to look authentic) but has perfect vector text

**Part B: Searching for Coherence (Signs of Legitimacy)**

This part is **equally critical** - prevents over-flagging legitimate documents:

1. **Holistic Consistency & Professionalism**:
   - Internal consistency: Branding/design/tone constant across pages?
   - Professional quality: High-quality design suggests legitimate origin
   - Counter-argument to deception signals

2. **Visual-Technical Coherence**:
   - Question: Do URLs align logically with visual representation?
   - Example: PayPal button → paypal.com (coherent) vs → sketchy-payment.ru (incoherent)
   - All major interactive elements must be checked

3. **Transparency & Good Faith**:
   - Clear, non-obfuscated links
   - Absence of high-pressure tactics
   - Honest communication style

**Input Evidence** (Specified in Prompt):
1. **Visual Evidence**: High-resolution PNG image of page (base64-encoded)
2. **Technical Blueprint**: Structured JSON "Element Map" containing:
   - Interactive element coordinates
   - Link text and destination URLs
   - Element types (annotation, text, qr_code)
3. **Forensic Context**: Briefing from previous pages with high-significance findings

**Output Requirements** (Enforced via Prompt + Schema Binding):
- Structured JSON conforming to `PageAnalysisResult` schema
- `technical_data` field as JSON string: `'{"url": "...", "xref": ...}'` (not plain text)
- URL prioritization with proper `source_context` and `extraction_method`
- **CRITICAL**: Report only current page findings (use previous context for reasoning only)

**Why This Structure**:
- **Structured Output**: Eliminates parsing errors, ensures consistency
- **JSON Technical Data**: Enables programmatic evidence extraction
- **Page Isolation**: Prevents double-counting findings across pages
- **Context Usage**: Cross-page coherence without contaminating per-page results

**Implementation**: `src/pdf_hunter/agents/image_analysis/prompts.py::IMAGE_ANALYSIS_SYSTEM_PROMPT`

### User Prompt Template

**Purpose**: Provides concrete evidence and structured mission for each page analysis.

**Template Structure**:
```
I need you to analyze the following PDF page for visual deception tactics.

---
Forensic Context from Previous Pages:
{previous_pages_context}
---
Technical Blueprint (Element Map for CURRENT page):
{element_map_json}

Your Mission:
1. Review forensic context
2. Examine visual evidence (attached image)
3. Cross-reference technical blueprint
4. Synthesize and decide

Provide complete analysis for CURRENT PAGE ONLY in PageAnalysisResult JSON format.
```

**Design Rationale**:
1. **Clear Separation**: Distinguishes previous context (for reasoning) from current data (for reporting)
2. **Structured Mission**: Four-step process guides analysis systematically
3. **Explicit Scope**: "CURRENT PAGE ONLY" prevents cross-contamination
4. **Format Enforcement**: Explicitly requests JSON output format

**Dynamic Content**:
- `{previous_pages_context}`: Generated from previous page's high-significance findings
- `{element_map_json}`: Current page's interactive elements with coordinates and URLs

**Why This Matters**:
- **Cross-Page Coherence**: Previous context enables multi-page attack detection
- **Visual-Technical Integration**: Element map enables cross-modal verification
- **Scope Control**: Prevents LLM from reporting stale findings
- **Consistency**: Same structure every page ensures reproducible analysis

**Implementation**: `src/pdf_hunter/agents/image_analysis/prompts.py::IMAGE_ANALYSIS_USER_PROMPT`

---

## Prompt Engineering Impact on System Performance

**Research Contribution**: This prompt engineering approach is a **critical innovation** that enables:

1. **High Detection Accuracy**: Two-sided framework catches both sophisticated and crude attacks
2. **Low False Positive Rate**: Legitimacy signals prevent over-flagging benign documents
3. **Explainable Results**: Structured output provides detailed reasoning for every verdict
4. **Cross-Modal Analysis**: Explicit prompts for visual-technical cross-examination
5. **Scalable Analysis**: Same prompts work across diverse document types without retraining

**Alternative Approaches Not Used** (and why):
- ❌ **Zero-shot classification**: No reasoning, no explainability, high false positive rate
- ❌ **Few-shot learning**: Requires curated examples, doesn't generalize well
- ❌ **Fine-tuned models**: Expensive, brittle, requires retraining for new attack patterns
- ✅ **Structured reasoning prompts**: Generalizable, explainable, maintainable

## LLM Configuration

**Model Provider**: Configurable via environment variables
- Supports OpenAI, Azure OpenAI, and other providers via LangChain's `init_chat_model()`
- Configuration centralized in `src/pdf_hunter/config/models_config.py`
- Temperature: 0.0 for deterministic, reproducible analysis
- Vision-capable model required for processing base64-encoded page images

**Structured Output Binding**:
```python
llm_with_structured_output = image_analysis_llm.with_structured_output(PageAnalysisResult)
```
This ensures all responses conform to the `PageAnalysisResult` schema, eliminating parsing errors and ensuring consistent data structure for downstream processing.

**Timeout Configuration**:
- `LLM_TIMEOUT_VISION = 120` seconds (configurable in `execution_config.py`)
- Protects against infinite hangs on vision API calls

**Message Format**:
```python
messages = [
    SystemMessage(content=IMAGE_ANALYSIS_SYSTEM_PROMPT),
    HumanMessage(
        content=[
            {"type": "text", "text": formatted_user_prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image.base64_data}"}
            }
        ]
    )
]
```

## Core Dependencies

### Multimodal AI
- **LangChain**: Message construction and structured output
  - `langchain_core.messages.SystemMessage`
  - `langchain_core.messages.HumanMessage`
  - `.with_structured_output()` for Pydantic binding

### Data Validation
- **Pydantic**: Schema enforcement and data validation
  - All data structures are Pydantic `BaseModel` subclasses
  - Field descriptions used for LLM output guidance

### Logging
- **Loguru**: Structured logging with JSONL output
  - Event-based logging for monitoring
  - Multiple severity levels for different findings
  - Automatic context propagation (agent, node, session_id)

### State Management
- **LangGraph**: State passing and workflow orchestration
  - `TypedDict` for state schemas
  - `operator.add` for list aggregation (errors)

### Serialization
- **Custom Serializer**: Safe JSON serialization
  - `dump_state_to_file()` from `pdf_hunter.shared.utils.serializer`
  - Handles Pydantic models and complex nested structures

## Integration Points

### Input from PDF Extraction Agent
**Required State Fields**:
- `extracted_images`: List of base64-encoded page images with phash metadata
- `extracted_urls`: List of URLs with coordinates and page numbers
- `number_of_pages_to_process`: Page limit for analysis
- `session_id`: Session identifier
- `output_directory`: Base output directory

### Output to URL Investigation Agent
**Provided State Fields**:
- `prioritized_urls`: URLs with priority scores (1-5)
  - Priority ≤ 5: Flagged for investigation
  - Includes `source_context` and `extraction_method`
  - Mission status tracking for loop prevention

### Output to Report Generator Agent
**Provided State Fields**:
- `visual_analysis_report`: Complete ImageAnalysisReport
  - Overall verdict and confidence
  - All aggregated findings (detailed, tactics, signals)
  - Document flow summary
  - Executive summary

**Report File**:
- Saved to: `{output_directory}/image_analysis/image_analysis_state_session_{session_id}.json`
- Contains complete serialized report for debugging and analysis

## Execution Configuration

**Recursion Limit**: 15
```python
IMAGE_ANALYSIS_CONFIG = {
    "run_name": "Visual Analysis Agent",
    "recursion_limit": 15  # Per-page analysis workflow
}
```

**Rationale**: Linear workflow with no loops, modest limit sufficient

**Implementation**: `src/pdf_hunter/config/execution_config.py`

## Key Design Decisions

### Why Cross-Page Context?
**Problem**: Attackers use multi-page narratives to build trust before exploitation (gradual trust-building followed by attack)
**Solution**: Each page receives high-confidence findings from previous pages, enabling coherence checking
**Principle Alignment**: Core implementation of "incoherence is a symptom" - enables detection of cross-page inconsistencies that reveal deception
**Benefit**: Detects sophisticated attacks where early pages establish legitimacy to make later pages more credible

### Why Sequential Analysis?
**Problem**: Attackers use multi-page narratives to build trust before exploitation (page 1-2 benign, page 3 malicious)
**Solution**: Sequential processing with context accumulation enables cross-page coherence checking
**Principle Alignment**: Implements "incoherence is a symptom" - detects narrative inconsistencies across pages
**Trade-off**: Slower execution, but higher detection accuracy for sophisticated multi-page attacks

### Why "Weakest Link" Confidence?
**Problem**: Averaging confidence dilutes critical warnings
**Solution**: Maximum confidence among pages with highest threat level
**Benefit**: Ensures high-confidence threats aren't masked by benign pages

### Why Structured Output?
**Problem**: Freeform LLM output unreliable for downstream processing
**Solution**: Pydantic schema binding with field descriptions
**Benefit**: Consistent, parseable output for URL Investigation and Report Generation

### Why URL Prioritization in This Agent?
**Problem**: Not all URLs warrant expensive browser investigation
**Solution**: Visual context enables intelligent priority assessment
**Benefit**: Focuses URL Investigation on truly suspicious URLs (reduces cost/time)

## Error Handling

### Timeout Errors
- **Trigger**: Vision LLM call exceeds 120 seconds
- **Handling**: Caught by `asyncio.wait_for()`, logged with timeout context
- **Recovery**: Returns error list, allows orchestrator to continue

### Missing Input Data
- **Trigger**: No extracted images available
- **Handling**: Early return with empty page analyses
- **Benefit**: Graceful degradation, no crashes

### LLM Failures
- **Trigger**: Structured output parsing errors, API failures
- **Handling**: Exception caught, logged with full context
- **Recovery**: Returns error list, preserves partial results

### File I/O Errors
- **Trigger**: Unable to create directory or save report
- **Handling**: Logged but doesn't crash compilation
- **Benefit**: Analysis completes even if persistence fails

## CLI Usage

```bash
# Run image analysis standalone
uv run python -m pdf_hunter.agents.image_analysis.graph --file test.pdf --pages 3

# With debug logging
uv run python -m pdf_hunter.agents.image_analysis.graph --file test.pdf --debug

# Get help
uv run python -m pdf_hunter.agents.image_analysis.graph --help
```

**Implementation**: `src/pdf_hunter/agents/image_analysis/cli.py`

## Testing

### Test Files
- Located in `tests/assets/pdfs/`
- Include phishing samples, benign documents, mixed-threat scenarios

### Test Scenarios
1. **Brand Impersonation**: Logo vs. URL mismatch detection
2. **Urgency Tactics**: Detection of time-pressure language
3. **Benign Documents**: False positive rate assessment
4. **Multi-Page Attacks**: Cross-page coherence tracking

### Manual Testing
```bash
# Test with known phishing sample
uv run python -m pdf_hunter.agents.image_analysis.graph --file tests/assets/pdfs/test_mal_one.pdf

# Test with benign document
uv run python -m pdf_hunter.agents.image_analysis.graph --file tests/assets/pdfs/hello_qr_and_link.pdf
```

## Future Enhancements

### Potential Improvements
1. **Parallel Page Analysis**: Trade cross-page context for speed (with separate coherence check)
2. **Adaptive Context Window**: Dynamic context based on document type
3. **Visual Similarity Detection**: Compare logos against known brand databases
4. **OCR Enhancement**: Extract text from images for better analysis
5. **Confidence Calibration**: Machine learning for better confidence scoring

## References

### Implementation Files
- **Nodes**: `src/pdf_hunter/agents/image_analysis/nodes.py`
- **Schemas**: `src/pdf_hunter/agents/image_analysis/schemas.py`
- **Prompts**: `src/pdf_hunter/agents/image_analysis/prompts.py`
- **Graph**: `src/pdf_hunter/agents/image_analysis/graph.py`
- **CLI**: `src/pdf_hunter/agents/image_analysis/cli.py`
- **Config**: `src/pdf_hunter/config/models_config.py`, `src/pdf_hunter/config/execution_config.py`

### Related Documentation
- **PDF Extraction**: How images and URLs are extracted
- **URL Investigation**: How prioritized URLs are analyzed
- **Report Generator**: How visual findings contribute to final report
- **Orchestrator**: How image analysis fits into overall pipeline
