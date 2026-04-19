# docflow-poc

Small Python proof of concept for a narrow document flow:

1. download one PDF from OneDrive or SharePoint with Microsoft Graph
2. extract page text plus any PDF annotations/markup that PyMuPDF can read
3. map the raw extraction into a strict JSON structure
4. populate a simple Word `.docx` template
5. upload the generated `.docx` back to OneDrive or SharePoint

The current version is intentionally narrow. It is a happy-path local CLI with deterministic mapping only.
The template can be read either from the local filesystem or from Microsoft storage via Graph.

## Project structure

```text
docflow-poc/
  function_app.py
  host.json
  src/
    config.py
    graph_client.py
    pdf_extractor.py
    mapper.py
    docx_generator.py
    main.py
    pipeline.py
    state_store.py
    trigger_service.py
  templates/
    report_template.docx
  output/
    .gitkeep
  resources/
  tests/
    test_mapper.py
  .env.example
  requirements.txt
```

## Assumptions

- This POC assumes Microsoft 365 business storage accessed through Microsoft Graph.
- Authentication uses an Entra app registration with client credentials.
- The simplest supported Graph addressing model is `drive_id + item_id` or `drive_id + path`.
- The input PDF already contains machine-readable text and/or PDF annotations.
- If Bluebeam comments were flattened into the PDF visually, this build falls back to plain text extraction and records that in logs and audit output.
- The included Word template is intentionally simple. It replaces a few placeholders and inserts an extracted-items table.

## Environment variables

Copy `.env.example` to `.env` and fill in the values.

Required:

- `DOCFLOW_GRAPH_TENANT_ID`
- `DOCFLOW_GRAPH_CLIENT_ID`
- `DOCFLOW_GRAPH_CLIENT_SECRET`

Optional defaults:

- `DOCFLOW_GRAPH_DRIVE_ID`
- `DOCFLOW_GRAPH_OUTPUT_DRIVE_ID`
- `DOCFLOW_OUTPUT_DIR` default: `output`
- `DOCFLOW_LOG_LEVEL` default: `INFO`
- `DOCFLOW_ENABLE_LLM_MAPPING` default: `false`

`DOCFLOW_ENABLE_LLM_MAPPING` is only a placeholder for later. This POC does not call an LLM.

Timer-trigger defaults:

- `DOCFLOW_INPUT_FOLDER_PATH` default: `Docflow/Input`
- `DOCFLOW_OUTPUT_FOLDER_PATH` default: `Docflow/Output`
- `DOCFLOW_TEMPLATE_FILE_PATH` default: `Docflow/template/report_template.docx`
- `DOCFLOW_TEMPLATE_DRIVE_ID` default: same as `DOCFLOW_GRAPH_DRIVE_ID`
- `DOCFLOW_POLL_SCHEDULE` default: `0 */1 * * * *`
- `DOCFLOW_STATE_CONTAINER` default: `docflow-state`
- `DOCFLOW_DELTA_LINK_BLOB_NAME` default: `drive-delta-link.txt`
- `DOCFLOW_PROCESSED_ITEMS_BLOB_NAME` default: `processed-items.json`
- `DOCFLOW_INITIAL_DELTA_MODE` default: `full_scan`

## Microsoft Graph permissions

For app-only client credential flow, the Entra app will usually need Graph application permissions along the lines of:

- `Files.Read.All` or `Files.ReadWrite.All`
- `Sites.Read.All` or `Sites.ReadWrite.All`

Exact permissions depend on how locked down the tenant is and where the drive lives. This repo does not create or configure the app registration.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

Run as a module so the `src` package imports cleanly:

```bash
python -m src.main \
  --drive-id YOUR_DRIVE_ID \
  --input-file-id YOUR_PDF_FILE_ID \
  --output-folder-id YOUR_OUTPUT_FOLDER_ID \
  --template-path templates/report_template.docx
```

Path-based example:

```bash
python -m src.main \
  --drive-id YOUR_DRIVE_ID \
  --input-file-path "Input/sample.pdf" \
  --output-folder-path "Output" \
  --template-path templates/report_template.docx
```

If the output folder is in a different drive, add `--output-drive-id`.

Template from OneDrive / SharePoint in the same drive:

```bash
python -m src.main \
  --input-file-path "Docflow/Input/sample.pdf" \
  --output-folder-path "Docflow/Output" \
  --template-file-path "Docflow/template/report_template.docx"
```

If the template is in a different drive, add `--template-drive-id`.

## Azure Function trigger

The repo now includes an Azure Functions timer entrypoint in [function_app.py](/Users/mikasiddiqui/Documents/GitHub/docflow-poc/function_app.py).

Trigger behavior:

- polls the configured drive on a timer using Microsoft Graph delta query
- filters for new or changed `.pdf` files under `DOCFLOW_INPUT_FOLDER_PATH`
- downloads the configured DOCX template from OneDrive / SharePoint
- generates the output DOCX and uploads it to `DOCFLOW_OUTPUT_FOLDER_PATH`
- stores the Graph delta link and processed file versions in the Function App storage account

Expected Azure app settings:

```env
DOCFLOW_GRAPH_TENANT_ID=...
DOCFLOW_GRAPH_CLIENT_ID=...
DOCFLOW_GRAPH_CLIENT_SECRET=...
DOCFLOW_GRAPH_DRIVE_ID=...
DOCFLOW_INPUT_FOLDER_PATH=Docflow/Input
DOCFLOW_OUTPUT_FOLDER_PATH=Docflow/Output
DOCFLOW_TEMPLATE_FILE_PATH=Docflow/template/report_template.docx
DOCFLOW_OUTPUT_DIR=/tmp/docflow
DOCFLOW_LOG_LEVEL=INFO
DOCFLOW_POLL_SCHEDULE=0 */1 * * * *
DOCFLOW_STATE_CONTAINER=docflow-state
DOCFLOW_DELTA_LINK_BLOB_NAME=drive-delta-link.txt
DOCFLOW_PROCESSED_ITEMS_BLOB_NAME=processed-items.json
DOCFLOW_INITIAL_DELTA_MODE=full_scan
```

Deployment note:

- The Function App uses `AzureWebJobsStorage` for its internal state store.
- For the first deployment, manual deploy is simpler than continuous deployment.
- `.funcignore` excludes local output, tests, virtualenv files, and synthetic example assets from Azure deploys.

Deployment command:

```bash
func azure functionapp publish YOUR_FUNCTION_APP_NAME --python
```

First-run behavior:

- `DOCFLOW_INITIAL_DELTA_MODE=full_scan` means the first timer run processes PDFs already in the input folder.
- `DOCFLOW_INITIAL_DELTA_MODE=latest` means the first timer run starts tracking from "now" and only processes later uploads.

## Outputs

Each run writes local artifacts into `output/`:

- `downloaded_input.pdf`
- `raw_extraction.json`
- `structured_content.json`
- `generated_report.docx`
- `run_audit.json`
- `run.log`

For simplicity, those files are overwritten on each run.

## Raw extraction shape

The raw extraction is intentionally inspectable. Example:

```json
{
  "source_file_name": "sample.pdf",
  "page_count": 2,
  "annotation_count": 1,
  "pages": [
    {
      "page": 1,
      "text": "Page text...",
      "annotations": [
        {
          "subtype": "Text",
          "kind": "annotation",
          "content": "Reviewer note",
          "author": "Tom",
          "subject": "Comment"
        }
      ]
    }
  ]
}
```

## Structured schema

The mapped JSON is the strict schema used by the DOCX step:

```json
{
  "source_file_name": "sample.pdf",
  "extracted_items": [
    {
      "page": 1,
      "type": "text",
      "content": "Page text...",
      "author": "",
      "subject": ""
    }
  ]
}
```

## Current limitations

- No OCR
- No retry logic
- No batch processing
- No database
- No frontend
- No Power Automate integration
- No LLM mapping yet
- Template handling is intentionally basic and assumes the included placeholder format

## Included sample assets

Synthetic sample files are included for local testing and demos:

- [resources/examples/stacc_floorplan_markup_sample.pdf](/Users/mikasiddiqui/Documents/GitHub/docflow-poc/resources/examples/stacc_floorplan_markup_sample.pdf)
- [templates/stacc_poc_report_template.docx](/Users/mikasiddiqui/Documents/GitHub/docflow-poc/templates/stacc_poc_report_template.docx)
- [resources/examples/sample_raw_extraction.json](/Users/mikasiddiqui/Documents/GitHub/docflow-poc/resources/examples/sample_raw_extraction.json)
- [resources/examples/sample_structured_content.json](/Users/mikasiddiqui/Documents/GitHub/docflow-poc/resources/examples/sample_structured_content.json)
- [resources/examples/sample_filled_report.docx](/Users/mikasiddiqui/Documents/GitHub/docflow-poc/resources/examples/sample_filled_report.docx)

These are synthetic examples designed to resemble a STACC-style marked-up plan review flow. They are not real client or STACC source documents.

## Test

```bash
python -m unittest discover -s tests
```
