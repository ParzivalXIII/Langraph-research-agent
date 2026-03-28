# Quickstart: Gradio Research UI

This guide gets you started with the Gradio research interface in under 5 minutes.

## Prerequisites

- Python 3.12+
- FastAPI backend running on `http://localhost:8000` (default)
- `uv` package manager

## Setup

### 1. Install Dependencies

```bash
cd /path/to/Langraph-research-agent
uv sync  # Installs all dependencies including gradio, httpx
```

If `uv` is not available, use `pip`:

```bash
pip install -e .
pip install gradio httpx
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
API_BASE_URL=http://localhost:8000
TIMEOUT=60
```

Or use defaults:

- `API_BASE_URL` defaults to `http://localhost:8000`
- `TIMEOUT` defaults to `60` seconds

### 3. Start the FastAPI Backend

In one terminal:

```bash
cd /path/to/Langraph-research-agent
uv run fastapi dev app/main.py
```

Or if you prefer standard Python:

```bash
python -m uvicorn app.main:app --reload
```

You should see the FastAPI server running at `http://localhost:8000`.

### 4. Start the Gradio UI

In a second terminal:

```bash
cd /path/to/Langraph-research-agent
uv run python ui/app.py
```

Gradio will print a URL like:

```
Running on local URL:  http://127.0.0.1:7860
```

Open that URL in your browser.

## Basic Usage

1. **Enter a Query**: Type your research question in the "Query" text box
   - Example: "What are the latest developments in AI agents?"

2. **Select Controls**:
   - **Depth**: Choose from "basic", "intermediate", or "deep"
   - **Max Sources**: Slider from 3 to 10
   - **Time Range**: Choose from "day", "week", "month", "year", or "all"

3. **Click "Run Research"**: The UI will send the request to the backend and wait for results

4. **Review Results**:
   - **Summary tab**: Read the synthesized answer
   - **Key Points tab**: Scan the bullet-point highlights
   - **Sources tab**: Examine the ranked references with relevance scores
   - **Diagnostics tab**: Check confidence score and any contradictions

## Troubleshooting

### "Unable to connect to backend"

- Ensure FastAPI is running on the correct URL (default: `http://localhost:8000`)
- Check `API_BASE_URL` in `.env` or environment variables
- Verify no firewall is blocking port 8000

### "Request timed out after 60 seconds"

- The backend is taking too long to respond
- Check backend logs for slow queries or Tavily lookups
- Increase `TIMEOUT` in `.env` if needed (not recommended; find root cause instead)

### "Invalid response from backend"

- The backend response doesn't match the expected schema
- Check backend logs for errors
- Verify you're using a compatible version of the backend

### "Error: Query is empty or whitespace only"

- The query field must contain at least one non-space character
- Provide a meaningful research question

## Project Structure

```
ui/
├── app.py                  # Gradio Blocks entry point
├── client/
│   └── api_client.py       # HTTP client to backend
├── components/
│   ├── controls.py         # Input controls (depth, sources, time_range)
│   ├── results.py          # Result rendering (summary, key_points, sources)
│   └── diagnostics.py      # Diagnostics display (confidence, contradictions)
└── models.py               # Pydantic models for request/response validation

tests/
├── unit/
│   ├── test_api_client.py
│   └── test_components.py
└── integration/
    └── test_research_flow.py
```

## Next Steps

- **Development**: Edit `ui/app.py` or component files and the Gradio server will hot-reload
- **Testing**: Run `pytest tests/` to validate client and component logic
- **Deployment**: See [docker-compose.yml](../../../docker-compose.yml) for production setup
- **Observability**: Check `ui/client/api_client.py` logs (stdout/stderr) for request/response details

## Common Development Tasks

### Add a New Output Component

1. Create a Gradio component (e.g., `gr.JSON()`)
2. Wire it into the `outputs=` list in the submit button click handler
3. Update the callback return tuple to match
4. Test with a mocked backend response

### Change the Layout

Edit the `with gr.Blocks() as demo:` section in `ui/app.py`:

- Use `gr.Row()`, `gr.Column()`, `gr.Tab()` to organize components
- Adjust label text, placeholder text, and slider ranges as needed

### Test with a Mock Backend

Modify `ui/client/api_client.py` to return hardcoded responses:

```python
async def research(self, payload: dict):
    # Mock response for testing
    return {
        "summary": "Sample summary...",
        "key_points": ["Point 1", "Point 2"],
        "sources": [{"title": "Test", "url": "https://example.com", "relevance": 0.9}],
        "contradictions": [],
        "confidence_score": 0.85
    }
```

## References

- [Gradio 6 Docs](https://www.gradio.app/docs/)
- [httpx Docs](https://www.python-httpx.org/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
