import os

import uvicorn

# ... your FastAPI app and routes ...

if __name__ == "__main__":
    # Get port from environment or default to 8000
    port = int(os.getenv("PORT", 8002))
    # In dev, you likely want reload=True. In Docker, start.sh will handle it.
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
