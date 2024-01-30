"""
Save the data to a SQLite3 database by periodically hitting the df command,
visualize the data using plotly-dash.

Usage:

```
uvicorn --host "0.0.0.0" --port 8881 main:app
```

Open browser and access 'localhost:8881/index'
"""
from dashapp import create_dash_app
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
import uvicorn

from dashapp import db_init, create_dash_app

VERSION = "v0.1.0"
app = FastAPI()


@app.get("/")
def read_main():
    return {
        "routes": [
            {
                "version": VERSION,
            },
            {
                "method": "GET",
                "path": "/",
                "summary": "Landing"
            },
            {
                "method": "GET",
                "path": "/status",
                "summary": "App status"
            },
            {
                "method": "GET",
                "path": "/index",
                "summary": "Sub-mounted Dash application"
            },
        ]
    }


@app.get("/status")
def get_status():
    return {"status": "ok"}


dash_app = create_dash_app(requests_pathname_prefix="/index/")
app.mount("/index", WSGIMiddleware(dash_app.server))

if __name__ == "__main__":
    db_init()
    uvicorn.run("main:app", host="0.0.0.0", port=8881)
