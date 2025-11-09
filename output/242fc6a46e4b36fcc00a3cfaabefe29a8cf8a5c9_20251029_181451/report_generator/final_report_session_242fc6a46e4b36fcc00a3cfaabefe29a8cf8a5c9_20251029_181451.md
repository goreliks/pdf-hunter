# Forensic Case Report

---

## 1. Final Verdict and Executive Summary

- **Verdict:** **Malicious**
- **Confidence Level:** 1.0 (High Confidence)
- **Reasoning Summary:**  
  A holistic review of all evidence reveals overwhelming, unambiguous proof of malicious intent. The static and structural analysis exposes a fully automated attack chain: the PDF's `/OpenAction` triggers a `/Launch` action that executes a hex-encoded Windows command. This command disables Windows Defender, downloads malware from a remote URL, establishes persistence, and cleans up evidence. The decoded payload and its behavior are preserved as artifacts, and the attack chain is mapped in detail. Visual and link analysis confirm that all visible links in the document point to legitimate Foxit vendor URLs, and these URLs are verified as benign by live web forensics. However, this is a classic case where the 'weakest link' principle applies: the presence of a weaponized `/Launch` action with a decoded, system-compromising payload is definitive. The benign appearance of the document and the use of legitimate vendor links serve as camouflage, but do not mitigate the core threat. The visual analysis correctly flags social engineering tactics (mimicking dialogs, urging users to override security), but the static analysis proves that user interaction is not even required for compromise. There are no meaningful contradictions between the agents; rather, the static analysis reveals the true, hidden intent behind the superficially benign content. The overall intent of the author is clear: to compromise the user's system via automated malware delivery and persistence, using deceptive visual cues as cover. This file is conclusively malicious.

- **Investigation Overview:**  
  The investigation encompassed static, structural, visual, and dynamic link analysis of a 27-page PDF, focusing on the first four pages. The file was found to contain a weaponized `/OpenAction` and `/Launch` action, which, upon opening, executes a decoded batch script that disables Windows Defender, downloads and installs malware, and establishes persistence. All visible links in the document point to legitimate Foxit vendor URLs, which were independently verified as benign. The document's visual design employs social engineering tactics to lower user defenses, but the technical payload is fully autonomous and does not require user interaction. All findings are corroborated across multiple analytic domains, leading to a conclusive malicious classification.

---

## 2. Case File Details

### Case & File Identifiers

- **Session ID:** `242fc6a46e4b36fcc00a3cfaabefe29a8cf8a5c9_20251029_181451`
- **File Path:** `/Users/gorelik/Courses/pdf-hunter/tests/assets/pdfs/87c740d2b7c22f9ccabbdef412443d166733d4d925da0e8d6e5b310ccfc89e13.pdf`
- **Output Directory:** `output/242fc6a46e4b36fcc00a3cfaabefe29a8cf8a5c9_20251029_181451`
- **PDF Hashes:**
  - **SHA1:** `242fc6a46e4b36fcc00a3cfaabefe29a8cf8a5c9`
  - **MD5:** `000d3c8a528505461dea43b3ead5f422`
  - **SHA256:** `87c740d2b7c22f9ccabbdef412443d166733d4d925da0e8d6e5b310ccfc89e13`

### Document Composition

- **Total Page Count:** 27
- **Pages Processed:** 4 (pages 0, 1, 2, 3)
- **Extracted Images:** 4 (one per processed page, all in PNG format)
- **Extracted URLs:** 5 (all pointing to official Foxit domains)
- **Structural Features:**
  - `/OpenAction` present (triggers on file open)
  - `/Launch` action present (executes external command)
  - No embedded JavaScript, no embedded files, no encryption
  - 10 URI objects in PDF structure
- **Notable Objects:**
  - `/ObjStm` with `/Launch` action
  - Decoded batch script and command artifacts extracted

---

## 3. Executive Summary

The investigation of the PDF file revealed a sophisticated, multi-stage attack chain embedded within the document's structure. Upon opening, the PDF automatically executes a Windows command that disables Windows Defender, downloads malware from a remote server, and establishes persistence by copying the malware to the system's Startup folder. The attack is fully automated and does not require user interaction, although the document employs social engineering tactics to encourage risky behavior. All visible links in the document point to legitimate Foxit vendor URLs, which were independently verified as safe. The malicious payload is hidden within the PDF's `/Launch` action, and its decoded contents are preserved as forensic artifacts. The investigation conclusively determines the file to be malicious, with all analytic domains in agreement.

---

## 4. Detailed Investigative Narrative

### Phase 1: Preprocessing and Static Triage

- **Initial Impression:**  
  The static triage flagged the PDF as suspicious due to the presence of `/OpenAction` and `/Launch` entries. These features grant the document autonomy to execute actions upon opening, which is a high-risk indicator. The triage reasoning followed the principle "Autonomy is Disease," warranting immediate, focused investigation.

### Phase 2: In-Depth Static Analysis

- **Structural Investigation:**  
  - The root `/Catalog` object contains an `/OpenAction` that points to a `/Launch` action.
  - The `/Launch` action references a Windows-specific object containing a hex-encoded command.
  - Decoding this command reveals a batch script that:
    - Disables Windows Defender real-time monitoring.
    - Downloads a remote executable (`Theme_Smart.scr`) from `https://badreddine67.000webhostapp.com/Theme_Smart.scr`.
    - Moves the downloaded file to the Windows Startup folder for persistence.
    - Deletes itself to erase evidence.
    - Creates and executes a VBScript to run the batch file silently, then deletes the VBScript.
  - The decoded batch script and command are preserved as artifacts.
  - The attack chain is fully automated and does not require user interaction.

- **Attack Chain (Step-by-Step):**
  1. **PDF Opened:** `/OpenAction` in `/Catalog` triggers `/Launch` action.
  2. **/Launch Action:** Executes Windows-specific parameters (object 7).
  3. **Command Decoded:** Batch script disables Defender, downloads malware, establishes persistence.
  4. **Malware Downloaded:** From `https://badreddine67.000webhostapp.com/Theme_Smart.scr`.
  5. **Persistence Established:** Malware moved to Startup folder, executed via VBScript.

### Phase 3: Visual Analysis

- **Overall Assessment:**  
  The visual analysis agent classified the document as "Suspicious" (confidence 0.78), with most pages individually benign but one (page 2) flagged for social engineering.
- **Document Layout & Purpose:**
  - **Page 0:** Bold cover page, no interactive elements.
  - **Page 1:** Introduction, recommends installing Foxit PDF Reader, includes legitimate links and branding.
  - **Page 2:** Step-by-step instructions with screenshots mimicking Foxit and Windows dialogs, urging the user to override security warnings and launch a file.
  - **Page 3:** Educational candlestick chart reference, with a full-page (invisible) link to the official Foxit site.
- **Deception Tactics Identified:**
  - Psychological manipulation (authority, social engineering) to encourage risky actions.
  - Visual mimicry of trusted dialogs to lower user defenses.
- **Signals of Legitimacy:**
  - All visible links point to official Foxit domains.
  - No evidence of brand impersonation in the links themselves.
  - Absence of urgency or fear-based language.

### Phase 4: Dynamic Link Analysis

- **URLs Investigated:**  
  All extracted URLs pointed to official Foxit domains:
  - `https://www.foxit.com/fr/pdf-reader/`
  - `https://www.foxit.com/`
- **Analyst Findings:**
  - Each URL was live-investigated using browser automation.
  - All loaded as expected, displaying official branding, product information, and standard legal links.
  - No suspicious redirects, forced downloads, overlays, or phishing forms were observed.
  - WHOIS lookups confirmed `foxit.com` as a long-established, reputable domain.
  - All URLs were conclusively classified as **benign**.

---

## 5. Correlated Threat Intelligence

- **Cross-Domain Confirmation:**
  - The static analysis revealed a weaponized `/Launch` action with a decoded, system-compromising payload. This was not visible in the document's visual layer, confirming the use of technical concealment.
  - The visual analysis identified social engineering tactics (mimicked dialogs, stepwise instructions) that correlate with the technical payload's intent: to lower user defenses and encourage risky behavior.
  - All visible links in the document were to legitimate Foxit domains, verified as benign by dynamic link analysis. This demonstrates the use of legitimate links as camouflage, increasing user trust while hiding the true threat in the document's structure.
  - No malicious URLs were found in the visible content; the only malicious URL (`https://badreddine67.000webhostapp.com/Theme_Smart.scr`) was embedded in the decoded batch script, not in any visible or clickable element.
  - The attack chain is fully autonomous: even if the user does not interact with the social engineering elements, the `/OpenAction` and `/Launch` ensure compromise upon opening the file.

- **Synthesis:**  
  The investigation demonstrates a classic case of technical and psychological deception working in tandem. The document's benign appearance and legitimate links serve as cover for a deeply embedded, fully automated malware delivery mechanism. The cross-domain analysis confirms that the true threat is hidden in the PDF's structure, not in its visible content or external links.

---

## 6. Evidence & Indicators of Compromise (IoCs)

### Evidence Log

**Extracted/Decoded Files:**
- **Decoded Batch Script:**  
  `/Users/gorelik/Courses/pdf-hunter/output/242fc6a46e4b36fcc00a3cfaabefe29a8cf8a5c9_20251029_181451/file_analysis/decoded_s_74h34h.bin`  
  *Description:* Batch script disables Defender, downloads and executes remote malware, establishes persistence, deletes itself, and uses VBScript for silent execution.

- **Decoded Malicious Command Artifact:**  
  `/Users/gorelik/Courses/pdf-hunter/output/242fc6a46e4b36fcc00a3cfaabefe29a8cf8a5c9_20251029_181451/file_analysis/decoded_hw1ngwjk.bin`  
  *Description:* Decoded command line for Windows CMD, as executed by the `/Launch` action.

**URL Investigation Screenshots:**  
- (Paths as referenced in the link analysis logs; actual file paths may vary by run environment)
  - `viewport_screenshot.png`
  - `fullpage_screenshot.png`
  - (Additional screenshots for each URL investigation, as saved in the MCP output directory)

**Other Preserved Artifacts:**  
- All decoded payloads and command artifacts referenced in the `master_evidence_graph`.

### Actionable Indicators of Compromise (IoCs)

- **Malicious Download URL:**
  - `https://badreddine67.000webhostapp.com/Theme_Smart.scr`
    - *Source:* Decoded batch script embedded in the PDF's `/Launch` action.

- **File Hashes:**
  - **PDF SHA1:** `242fc6a46e4b36fcc00a3cfaabefe29a8cf8a5c9`
  - **PDF MD5:** `000d3c8a528505461dea43b3ead5f422`
  - **PDF SHA256:** `87c740d2b7c22f9ccabbdef412443d166733d4d925da0e8d6e5b310ccfc89e13`

- **No additional IoCs** (domains, hashes, or URLs) were found in the visible content or dynamic link analysis.

---

**End of Report**