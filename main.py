from dashapp import create_dash_app
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
# from fastapi.staticfiles import StaticFiles
# import asyncio
import uvicorn

from dashapp import db_init, create_dash_app

app = FastAPI()

# def plot_graph():
#     df = pd.read_csv("disk_usage.csv")
#     cf.set_config_file(theme='ggplot')
#     df.iplot(kind='scatter', x='Timestamp', y='Used')
#
#     return cf.iplot(df, filename='disk-usage')

# @app.get("/")
# async def root():
#     conn = sqlite3.connect("disk_usage.db")
#     df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)
#     conn.close()
#
#     cf.set_config_file(theme="ggplot")
#     df.iplot(kind="scatter", x="timestamp", y="used")
#     return cf.iplot(df, filename="disk-usage")

# async def main_loop():
#     while True:
#         data = run_df()
#         print(data)
#         await asyncio.sleep(6)


@app.get("/")
def read_main():
    return {
        "routes": [
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
