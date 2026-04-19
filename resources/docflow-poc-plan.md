# docflow-poc — Detailed Plan

## 1. Goal

Build a **simple, narrow proof of concept** that shows the core STACC workflow can be automated.

### POC outcome
A user places a Bluebeam PDF into a Microsoft OneDrive / SharePoint input folder. The system:

1. downloads the file,
2. extracts the relevant content in a structured way,
3. inserts that content into a predefined Word template,
4. generates a `.docx` report,
5. uploads the completed `.docx` into an output folder.

For the **first pass**, there is **no rewriting** and **no intelligent drafting**. It is effectively a structured **copy / map / populate** workflow.

---

## 2. What we are optimizing for

This POC is being designed for:

- **simplicity**
- **speed**
- **low risk**
- **easy demoability**
- **Microsoft ecosystem alignment**
- **clear path to production later**

This is **not** a full product build.
This is **not** a broad AI automation platform.
This is **not** the final production architecture.

It is a focused demonstration that the most painful administrative bottleneck can be automated.

---

## 3. Scope

### In scope for the POC

- One input folder in OneDrive or SharePoint
- One or a small number of representative Bluebeam/PDF files
- One fixed output Word template
- Deterministic extraction where possible
- Strict structured mapping
- Word document generation
- Uploading output back to Microsoft storage
- Basic logs / audit output

### Explicitly out of scope for the POC

- Rewriting or summarising findings
- Handling every STACC document type
- Complex branching logic across many report variants
- Full user interface
- Multi-user access control / admin console
- Full production error handling
- Full QA workflow / approvals workflow
- Long-term hosting hardening
- Cost optimisation beyond basic sensible choices

---

## 4. Working assumptions

1. The Bluebeam files contain extractable information, ideally as standard PDF text and/or annotations.
2. The target Word document can be represented as a stable template.
3. The first useful outcome is to move content from Bluebeam/PDF into the Word report structure with minimal transformation.
4. A human still reviews the final document.
5. STACC prefers to remain inside the Microsoft 365 ecosystem wherever possible.

If assumption 1 is false and files are heavily flattened or image-based, the pipeline will need OCR / vision fallback. That is still possible, but the simplest happy path is direct extraction first.

---

## 5. Recommended POC architecture

```text
Input folder (OneDrive / SharePoint)
        ↓
Microsoft Graph download
        ↓
PDF / Bluebeam extraction
        ↓
Structured JSON mapping
        ↓
Populate Word template (.docx)
        ↓
Upload .docx to output folder
        ↓
Upload audit JSON / run log
```

### Key principle
Keep the pipeline **linear and inspectable**.
Every step should be visible and testable on its own.

---

## 6. Technology choices

## 6.1 Core language
**Python**

Reason:
- fastest to build
- strong PDF tooling
- strong Word tooling
- easy local demo
- easy later migration into Azure Functions or container

## 6.2 Microsoft integration
**Microsoft Graph API**

Use Graph for:
- reading files from OneDrive / SharePoint
- writing generated files back
- optionally listing folders / selecting latest file later

## 6.3 PDF / Bluebeam extraction
Start with:
- **PyMuPDF** (`fitz`) and/or
- **pypdf**

Goal:
- extract raw text
- inspect annotations/comments if present
- capture page-level content where possible

## 6.4 Word generation
**python-docx**

Goal:
- load an existing `.docx` template
- replace placeholders
- populate tables or repeated sections
- save final `.docx`

## 6.5 Model usage
For the initial POC:
- **prefer no model if possible**
- only use a model if the extraction needs help mapping text into a rigid schema

If needed, use:
- **Azure OpenAI**
- a small, cheap model
- strict JSON schema output only

The model must not be used to invent wording. It should only help organise extracted content into predefined fields.

---

## 7. Recommended hosting approach

## POC / demo
**Run locally on laptop**

Reason:
- quickest path to working demo
- zero hosting setup friction
- easier debugging live
- still integrates with Microsoft services properly

## Later production direction
**Azure Function** or **small Azure-hosted service**

Reason:
- aligns with Microsoft stack
- easy to explain
- low operational complexity
- suitable for event-driven file processing

For now, do **not** overbuild hosting.

---

## 8. POC flow in detail

## Step 1 — Input file
A Bluebeam/PDF file is uploaded into a known Microsoft folder.

For the POC demo, this can simply be:
- a known OneDrive folder, or
- a known SharePoint document library folder

## Step 2 — File retrieval
The Python app authenticates using Entra credentials and downloads the file via Microsoft Graph.

## Step 3 — Extraction
The PDF is analysed.

Priority order:
1. direct text extraction
2. annotation/comment extraction
3. page-level grouping
4. fallback OCR/vision only if necessary

Output at this stage should be raw extracted content saved to disk for inspection.

Example raw output:

```json
{
  "source_file": "sample.pdf",
  "pages": [
    {
      "page": 1,
      "text": "...",
      "annotations": ["...", "..."]
    }
  ]
}
```

## Step 4 — Structured mapping
Convert raw extracted content into a stable schema that matches the Word template.

Example schema:

```json
{
  "project_name": "Example Project",
  "report_title": "Draft Compliance Report",
  "issues": [
    {
      "page": 3,
      "heading": "Access issue",
      "clause": "D4.3",
      "note": "Door width does not comply"
    }
  ]
}
```

For the first version, this mapping should be as deterministic as possible.

## Step 5 — Template population
Load a predefined `.docx` template and insert the structured values.

This may include:
- replacing placeholders like `{{project_name}}`
- filling a findings/issues table
- adding repeated rows for extracted issues

## Step 6 — Output generation
Save the final `.docx` locally.

## Step 7 — Upload
Upload the final `.docx` to the output Microsoft folder.

## Step 8 — Audit output
Upload or save:
- extracted JSON
- mapped JSON
- run log

This is important because the existing manual step also acts as QA.

---

## 9. Recommended repository structure

```text
/docflow-poc
  /app
    config.py
    main.py
    graph_client.py
    pdf_extractor.py
    mapper.py
    docx_builder.py
    models.py
    utils.py
  /templates
    report_template.docx
  /samples
    input/
    output/
  /artifacts
    extracted/
    mapped/
    logs/
  .env.example
  requirements.txt
  README.md
```

### Purpose of each module

- `main.py` — orchestration entry point
- `graph_client.py` — Microsoft Graph download/upload logic
- `pdf_extractor.py` — PDF text/annotation extraction
- `mapper.py` — raw extraction → structured fields
- `docx_builder.py` — populate Word template
- `models.py` — data schemas / types
- `config.py` — environment configuration

Keep each file narrow and obvious.

---

## 10. Suggested implementation phases

## Phase A — one-day demo build

### Goal
Show an end-to-end happy path.

### Deliverables
- local runnable script
- Graph integration working
- one real sample processed
- output `.docx` generated and uploaded
- simple logs and JSON artifacts

### Day-build order
1. Create repo and environment
2. Add Graph authentication + file download
3. Test PDF extraction on real sample
4. Define fixed JSON schema
5. Build `.docx` placeholder replacement
6. Add repeated issue row insertion if needed
7. Add upload to output folder
8. Add logs / audit artifacts
9. Dry run the demo end-to-end

## Phase B — POC hardening (1–2 weeks)

### Goal
Turn the one-day build into a clean proof of concept.

### Deliverables
- better error handling
- support for a few sample files
- stronger schema validation
- clearer template logic
- cleaner logging
- documented setup / run process
- packaged demo script

## Phase C — productionised version (6–8 weeks)

### Goal
Move from demo to reliable internal automation.

### Deliverables
- hosted execution
- trigger-based processing
- secure secret handling
- retry logic
- approval / review workflow
- folder rules
- support for more report variations
- monitoring and audit trail
- testing across real project samples
- handover / documentation

---

## 11. Detailed timeline suggestion

## 1-day build

### Day 1
- repo scaffold
- connect to Microsoft Graph
- process one sample PDF
- generate one Word output
- upload result
- prepare live demo

## 1–2 week POC

### Week 1
- stable sample coverage
- cleaner extraction and mapping
- template iteration
- better structure and logs

### Week 2
- improve reliability
- refine edge cases
- document setup
- prepare client-facing walkthrough and architecture diagram

## 6–8 week productionised build

### Weeks 1–2
Discovery, sample gathering, confirm templates, confirm data shapes

### Weeks 2–4
Build reliable extraction + mapping + document generation service

### Weeks 4–6
Harden edge cases, permissions, storage flows, logging, human review path

### Weeks 6–8
Testing, rollout, support, handover, production adjustments

---

## 12. Recommended data model

Keep the schema minimal.

Example:

```json
{
  "source_filename": "project_001.pdf",
  "project_name": "Project Name",
  "client_name": "Client Name",
  "report_type": "Access Report",
  "issues": [
    {
      "id": "ISSUE-001",
      "page": 2,
      "reference": "D4.3",
      "title": "Door width",
      "description": "Door width shown on drawing is insufficient"
    }
  ]
}
```

For the POC, avoid broad semantic fields. Only include fields needed by the template.

---

## 13. Error handling strategy

For the POC, keep errors simple and explicit.

Examples:
- file not found
- authentication failed
- no extractable content
- template placeholder missing
- upload failed

Do not hide failures.
Make them obvious in logs and console output.

---

## 14. Cost expectations

## POC
Very low cost.

Likely components:
- local laptop compute
- Microsoft Graph API usage
- negligible storage
- optional minimal model cost if used

## Production quick win
Still likely low cost if built narrowly.

Main cost drivers later:
- hosting/runtime
- document volume
- OCR / vision usage if many files are flattened
- model usage if schema mapping is delegated to an LLM

The most cost-effective version is:
- deterministic extraction first
- minimal model usage only where needed

---

## 15. Risks and mitigations

## Risk 1 — Bluebeam content is hard to extract
**Mitigation:** test real files immediately; prioritise annotations/text extraction before any model usage.

## Risk 2 — Word template is more variable than expected
**Mitigation:** start with one locked template; solve one report family first.

## Risk 3 — Manual process contains hidden QA logic
**Mitigation:** preserve raw extraction and audit JSON; keep human review in the loop.

## Risk 4 — Too much scope gets added too early
**Mitigation:** keep the first phase strictly “copy / map / populate.”

## Risk 5 — Microsoft permissions slow things down
**Mitigation:** use your own Entra/M365 setup first for the demo; only generalise later.

---

## 16. Demo plan for the meeting

The demo should be short and concrete.

### Suggested demo script
1. Show input folder in OneDrive / SharePoint
2. Show sample Bluebeam/PDF file
3. Run the script
4. Show log output:
   - downloaded file
   - extracted content
   - generated structured JSON
   - populated Word template
   - uploaded output
5. Open the output folder
6. Open generated `.docx`
7. Show audit JSON/log artifact
8. Explain what would be hardened in production

### Key message
“This proves the core bottleneck can be automated. The remaining work is reliability, QA, edge cases, hosting, and rollout.”

---

## 17. What not to do

To keep this simple, avoid the following in the first POC:

- complex workflow engines
- multi-step approval UIs
- SharePoint webhooks on day one
- fancy frontend dashboards
- broad document intelligence layers
- aggressive use of LLMs
- trying to handle all report types at once
- overcomplicated schema design
- introducing unnecessary third-party SaaS tools

---

## 18. Immediate next steps

1. Create the repo: `docflow-poc`
2. Set up Python environment
3. Add `.env` values for Entra / Graph
4. Test Graph download from one Microsoft folder
5. Test extraction on one real Bluebeam PDF
6. Define the smallest possible JSON schema
7. Prepare one Word template
8. Build the `.docx` generation step
9. Upload the result to output folder
10. Rehearse the demo

---

## 19. Success criteria for this POC

The POC is successful if:

- it runs end-to-end on at least one representative file
- it reads from Microsoft storage
- it generates a valid Word document in the target structure
- it uploads the output back to Microsoft storage
- it is understandable to a non-technical client
- it proves that the narrow workflow is viable

---

## 20. Final recommendation

The winning move is not to impress them with complexity.
The winning move is to show:

- clear thinking,
- strong autonomy,
- fast execution,
- narrow scoping,
- Microsoft-aligned architecture,
- and a real working artifact.

Build the smallest thing that proves the core path works.
That is what gives you the edge over the competitor.
