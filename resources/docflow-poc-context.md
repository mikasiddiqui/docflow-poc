# docflow-poc — consolidated context and briefing

This document consolidates the most important information from:
- the STACC candidate/job brief
- the business process flow / flowchart
- our current understanding of the contract
- the latest conversation updates after your call with them

It is intended to be a fast reference document for planning, scoping, pitching, and building the POC.

---

## 1. Contract summary

STACC is a small boutique building code and accessibility consultancy that is already operating at capacity. They are not struggling to win work — they are constrained by delivery throughput.

The main bottleneck is the manual step where findings from Bluebeam-marked plan reviews are transferred into structured Microsoft Word compliance reports. That transfer is slow, repetitive, and admin-heavy, even after the actual technical review work has already been completed.

The goal of this contract is to automate that workflow safely and pragmatically, starting with the narrowest high-value slice.

### What success means
At the highest level, success means:
- removing or materially reducing the manual Bluebeam-to-Word data-entry bottleneck
- preserving trust and accuracy for legal/compliance reporting
- freeing up STACC to take on more work
- doing this in a way that fits their existing Microsoft 365 environment
- building a lean first version that can later be hardened and potentially expanded

The longer-term upside is that, if this works well internally, the workflow could later be productised into a broader software/service offering.

---

## 2. What STACC currently does

### Team / environment
STACC is a small, busy, non-technical consultancy. The key stakeholders mentioned so far are:
- **Tom and Aaron** — founders / code consultants
- **Rachel** — support / drafting

Their current working environment is heavily based around:
- Microsoft Word
- OneDrive / SharePoint / Microsoft 365
- Bluebeam PDFs
- email

They do not want a complicated external-tool ecosystem if it can be avoided.

---

## 3. Current business process

Below is the current workflow based on the written business process notes and the flowchart.

## 3.1 Initial contact / prospect stage
A request comes in, usually via email and attachments, sometimes also via phone.

The PA sets up:
- prospect folder
- draft fee
- contract / proposal materials

STACC has fee proposal templates for many scenarios. A director reviews and amends scope and fees, then issues the proposal. For repeat clients, they look back at prior projects to keep fees/scopes consistent.

Once accepted, the prospect becomes a project.

### Why this matters
This explains that their business already relies on reusable templates, prior examples, and structured admin handoff. That means automation that plugs into a templated environment is a natural fit.

---

## 3.2 Design phase
This is where the main current bottleneck sits.

Typical steps:
- attend meetings and respond to RFIs
- inspect existing buildings if relevant
- carry out detailed assessment of plans in Bluebeam
- prepare mark-ups in Bluebeam
- summarise compliance issues in table format in Word if issuing a report
- Rachel / PA drafts the report structure and client/project details
- technical findings from mark-ups and summary tables are manually entered into the report template
- client reviews and revised versions are issued later as draft/final

### Important nuance
The manual transfer from Bluebeam into Word can take a long time **even after the substantive review work is already finished**.

This is the exact pain point the contract is targeting.

### Important QA nuance
This manual report-writing step also acts as a kind of QA pass. As they transfer the issues, they are effectively checking that they have not missed anything.

This means automation cannot just focus on speed. It must also preserve confidence, traceability, and reviewability.

---

## 3.3 Performance solution phase
Some jobs involve performance solutions rather than purely deemed-to-satisfy compliance.

Typical flow:
- a non-compliance is identified
- a PBDB (Performance Based Design Brief) is prepared, usually using a comparable previous report as a template
- after stakeholder review/concurrence, a formal Performance Solution Report is issued

### Why this matters
This is useful context, but it is probably **not** where the first quick-win POC should start.

These reports are more bespoke and more variable. They are better candidates for later phases once the narrow Bluebeam-to-Word pipeline is proven.

---

## 3.4 Construction phase
Some jobs include site inspections during construction.

Typical flow:
- attend meetings / RFIs
- carry out progress inspections
- take notes and photos on site
- PA drafts inspection report shell
- technical inspection findings are inserted

### Why this matters
This hints at later automation opportunities involving photos, inspection notes, and templated reporting — but again, it is likely out of scope for the first POC.

---

## 3.5 Completion phase
Some jobs involve final inspections and completion statements.

Typical flow:
- attend meetings / RFIs
- final site inspection
- draft inspection report
- review client close-outs
- PA drafts completion statement based on close-outs and certificates

### Why this matters
This reinforces a repeated pattern across the business:
- technical review work happens
- a structured document then has to be assembled manually from that work

That pattern is important for long-term roadmap thinking, but first phase should stay narrow.

---

## 4. Core bottleneck

The contract is really about one repeated pattern:

1. technical assessment is completed in Bluebeam
2. the findings already exist in some form
3. those findings must then be transferred into a rigid Word document
4. that transfer is manual and slow
5. STACC loses time on admin rather than high-value consulting work

So the first and most valuable slice is not “AI writing compliance advice.”

It is:
- extract what is already there
- structure it cleanly
- place it into the correct Word template
- keep it auditable

---

## 5. Job brief / role understanding

From the candidate brief, the role is effectively asking for someone who can:
- deconstruct the workflow precisely
- understand the formatting and logic requirements end to end
- extract messy data from Bluebeam PDFs
- build reliable, low-hallucination structured-processing logic
- generate correctly formatted Word output
- design the first version to work with OneDrive while leaving room for later scale/productisation

### Key role expectations
The founders are non-technical, so a big part of the role is translating technical design into:
- simple explanation
- business value
- clear tradeoffs
- pragmatic implementation

### Cultural / working style expectations
They want somebody who can:
- work autonomously
- not require constant check-ins
- move quickly
- make sensible technical decisions without a lot of hand-holding

This is important. The contract is not just about technical skill. It is also about being trusted to own the problem.

---

## 6. Updated understanding from your latest call

The latest call sharpened the scope substantially.

### 6.1 There is a direct competitive situation
It is between you and one other candidate.

They will go with the person they believe can best deliver.

This means the fastest way to differentiate is not talking more — it is showing a working implementation and a clearer plan.

### 6.2 They want a quick win first
They do **not** need the full grand vision immediately.

They want early validation that the core bottleneck can be automated.

Specifically, if the first version can simply:
- ingest a Bluebeam file from OneDrive / SharePoint
- extract the information in a structured way
- place it into their Word template
- upload the completed document back into Microsoft storage

then that is enough validation to justify next steps.

### 6.3 First pass should be extremely simple
The first pass should **not** try to rewrite or improve the content.

It should basically be:
- extract
- map
- insert

This is much closer to controlled copy/paste than content generation.

That is the right decision because it minimizes hallucination risk and keeps the POC easy to understand.

### 6.4 They want Microsoft-first
They use Microsoft 365 and want to stay in that ecosystem where possible.

That means:
- OneDrive / SharePoint for file storage
- Entra / Azure identity for auth
- likely Azure-hosted compute for later production
- likely Azure OpenAI if model usage is needed

They are not looking for a pile of third-party SaaS tools unless there is a very strong reason.

### 6.5 They have not fully thought through hosting / architecture
They are non-technical and are looking to you for guidance.

This means the contract is partly:
- solution design
- workflow design
- hosting recommendation
- implementation
- rollout thinking

### 6.6 Your communicated timelines were accepted
You told them:
- **POC:** 1–2 weeks
- **fully working, productionised, tested version:** 6–8 weeks

They were happy with these timelines.

### 6.7 Your current strategic move
You want to go even further and build a same-day demonstration before the next meeting so you can show:
- the path works
- you understand the architecture
- you can move fast
- you can operate independently

This is a very strong move if positioned correctly.

---

## 7. Agreed first POC scope

The narrow POC scope is now effectively:

### Input
A Bluebeam/PDF file appears in an input OneDrive or SharePoint folder.

### Processing
The system:
- downloads the file
- extracts notes / findings / relevant content
- converts that content into a fixed structured representation
- inserts the extracted content into a Word template

### Output
The system:
- generates a `.docx` output file
- uploads it into a target OneDrive / SharePoint folder

### Important constraints
- no rewriting on first pass
- keep it as deterministic as possible
- preserve traceability
- keep it super simple
- happy-path POC is acceptable

---

## 8. Recommended positioning in front of STACC

The right way to frame the POC is:

> This demonstrates that the core automation path is viable now. The remaining work in a real production version is hardening, edge cases, QA, permissions, monitoring, security, rollout, and template coverage.

This is better than implying the problem is already fully solved.

That framing makes you look:
- credible
- pragmatic
- honest
- senior enough to understand the difference between a demo and production

---

## 9. Technical approach — simplest path

## 9.1 Principle: keep it simple
The first version should be the smallest thing that proves the bottleneck can be removed.

That means avoiding:
- unnecessary UI
- unnecessary workflow engines
- unnecessary databases
- unnecessary orchestration layers
- complex multi-step agent systems
- any rewriting or “smart” report generation beyond strict mapping

## 9.2 Best POC shape
A very simple happy-path pipeline:

1. authenticate to Microsoft Graph using your Entra app
2. download a selected PDF from OneDrive / SharePoint
3. extract annotations / text / issues from the Bluebeam document
4. map to structured JSON
5. insert the fields/issues into a Word template
6. upload the resulting `.docx` back to Microsoft storage
7. optionally upload an audit JSON/log alongside it

## 9.3 Best implementation language
Python is the best fit for the POC because it is fastest to stand up and easiest to debug.

## 9.4 Likely key libraries / services
- **Microsoft Graph API** for file download/upload
- **PyMuPDF / pypdf** for PDF inspection and extraction
- **python-docx** for creating/filling Word documents
- **Azure OpenAI** only if needed for strict extraction-to-JSON mapping

---

## 10. Model usage philosophy

For the first POC, model use should be minimal.

### Best case
Do not use an LLM at all if the Bluebeam content can be extracted deterministically.

### If a model is needed
Use it only for constrained structured mapping, not for freeform writing.

For example:
- raw notes / extracted blocks go in
- strict JSON schema comes out
- your code inserts that into Word

The model should **not** be used to invent or improve compliance language in the first phase.

---

## 11. Hosting approach

## 11.1 For the immediate demo
Run it locally on your machine.

This is the fastest way to produce something you can screen-share.

It also keeps the demo simple:
- local script/app
- Graph auth
- input folder
- output folder
- generated document

## 11.2 For the likely production v1
A strong Microsoft-aligned production path would be:
- SharePoint / OneDrive input folder
- Azure Function or similar lightweight Azure compute
- Microsoft Graph file handling
- optional Azure OpenAI for structured extraction
- output document returned to SharePoint / OneDrive
- optional email / Teams notification

This gives them a clean story without introducing a lot of external tooling.

---

## 12. Risks and unknowns

These are the main practical risks / unknowns to test early.

### 12.1 Bluebeam extraction format
The biggest technical unknown is whether their Bluebeam markups/comments are stored as proper PDF annotations / machine-readable content, or whether some of it is flattened visually.

If the annotations are machine-readable, the POC path becomes much easier.

If they are flattened, extraction becomes harder and may require OCR or vision fallback.

### 12.2 Template variability
Some report types are more standardized than others.

Access Reports sound more templated and repeatable.
BCA reports may vary more and may use recent comparable reports as the template rather than one universal form.

That means the first POC should ideally target:
- one specific report type
- one consistent template family
- one narrow happy path

### 12.3 QA and trust
Because the current manual process doubles as QA, STACC may worry that automation removes an important review step.

The response to this is not “fully automate everything.”
The response is:
- preserve auditability
- keep raw extracted findings visible
- keep a human review step before issue to client

### 12.4 Permissions / Microsoft setup
Graph / SharePoint / OneDrive integration requires the right app registration, scopes, and folder/file paths.

This is manageable, but should be kept as simple as possible in the POC.

---

## 13. Why your current plan is strong

Your plan is strong because it aligns with what they explicitly care about:

### 13.1 It shows autonomy
Instead of just discussing architecture, you are showing them a working implementation.

### 13.2 It matches their quick-win mindset
You are focusing on the exact narrow bottleneck they want validated first.

### 13.3 It keeps scope honest
You are not pretending to have solved the entire business process. You are solving the first high-value slice.

### 13.4 It fits their ecosystem
The POC is aligned to Microsoft 365 rather than bolting on unrelated infrastructure.

### 13.5 It supports your previously given timeline
A same-day/demo prototype makes the 1–2 week POC estimate and 6–8 week production estimate feel credible rather than theoretical.

---

## 14. How to think about phases

## Phase 0 — same-day demo / screen-share proof
Goal:
- prove the core path works on a sample document

Outcome:
- Bluebeam/PDF in
- structured extraction
- Word out
- file uploaded back to Microsoft storage

## Phase 1 — 1 to 2 week POC
Goal:
- clean up the happy path
- improve template fidelity
- make the run more repeatable
- handle one or two document types reliably
- add basic logs / audit outputs

## Phase 2 — 6 to 8 week productionised version
Goal:
- harden permissions and deployment
- improve edge-case handling
- improve extraction reliability
- add monitoring / error handling
- add review flow and operational polish
- test against more real files / templates

---

## 15. Recommended message to yourself when building

Keep asking:

> What is the simplest thing that proves the Bluebeam-to-Word bottleneck can be automated inside a Microsoft-style workflow?

If a feature does not help answer that question, it probably belongs later.

---

## 16. Suggested repo framing

Current repo direction:
- **docflow-poc**

Reason:
- generic enough to keep public
- does not expose STACC
- clearly describes the narrow proof-of-concept nature

---

## 17. What this project is not, yet

For now, this project is **not**:
- a full SaaS product
- a generic document AI platform
- a full end-to-end STACC operations system
- an autonomous compliance writer
- a no-human-in-the-loop issuance system

It is a narrow workflow automation proof that can later expand.

That distinction matters and should stay clear in documentation and in conversation.

---

## 18. Condensed takeaway

If you need the shortest possible summary later, it is this:

STACC is a busy, non-technical consultancy whose bottleneck is manually transferring Bluebeam review findings into Word reports. The first win is not generative AI writing — it is controlled extraction and templated insertion inside a Microsoft 365 workflow. They want someone autonomous who can guide the architecture and deliver quickly. The best immediate move is a same-day happy-path POC showing: PDF from OneDrive/SharePoint in, structured extraction, `.docx` out, uploaded back to Microsoft storage. Production value then comes from hardening, QA, permissions, testing, and broader coverage.

