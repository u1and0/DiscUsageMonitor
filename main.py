#!/usr/bin/python3
"""
Save the data to a SQLite3 database by periodically hitting the df command,
visualize the data using plotly-dash.

Usage:

```
uvicorn --host "0.0.0.0" --port 8881 main:app /mnt/z
```

Open browser and access 'localhost:8881/index'
"""
import os
import asyncio

from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
import uvicorn

from dashapp import create_dash_app, db_init, load_data, \
    save_data, INTERVAL_SEC, DB_NAME

VERSION = "v0.1.1r"
app = FastAPI()

# Check mount point for monitoring
MNT_POINT = "/dev/mmcblk0p2"
if not os.path.exists(MNT_POINT):
    raise OSError(f"{MNT_POINT} not found")


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


# Create table if not exist
db_init()

df = load_data(DB_NAME)
loop = asyncio.get_event_loop()
loop.create_task(save_data(MNT_POINT, INTERVAL_SEC))

dash_app = create_dash_app(df, requests_pathname_prefix="/index/")
app.mount("/index", WSGIMiddleware(dash_app.server))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8881)
