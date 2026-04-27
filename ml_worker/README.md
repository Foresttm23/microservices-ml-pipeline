# ML Worker

This service accepts tasks, calls Gemini for inference, and returns/publishes a result payload that includes
`interaction_id` for cross-service tracing.

## Environment Variables

- `GEMINI_API_KEY`: Required for live Gemini calls.
- `GEMINI_MODEL`: Optional model override (default: `gemini-2.0-flash`).
- `GEMINI_API_BASE`: Optional API base URL (default: Google Generative Language API v1beta).
- `GEMINI_TIMEOUT_SECONDS`: Request timeout in seconds (default: `30`).
- `ML_WORKER_DRY_RUN`: `true`/`false`; when true, skips external API calls.

## Quick Local Run

From repository root:

```powershell
uv run python -m ml_worker.app.main
```