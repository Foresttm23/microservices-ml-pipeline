import os

import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    # We point to "app.main:app" so uvicorn knows where the instance is
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
