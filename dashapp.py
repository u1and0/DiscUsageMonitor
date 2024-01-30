import os
import subprocess
import sqlite3
import datetime
import asyncio

import flask
import pandas as pd

import dash
from dash.dependencies import Input, Output, State
import dash_table
from dash import dcc, html
import plotly.graph_objs as go

TITLE = "Disc Usage Monitor"
DESCRIPTION = "\\\\ns5のディスク容量を可視化します。"
MNT_POINT = "/mnt/z"
TABLE_NAME = "data"
INDEX_COL = "timestamp"
DB_NAME = "disk_usage.db"
INTERVAL_SEC = 10
"""
LIMIT_ROWについて
    10秒ごとにdf取得
    *360 件 == 1H
    *24 = 8640件 == 1day
    *365 = 3_153_600件 == 1year
"""
LIMIT_ROW = 8640


def db_init():
    """ DB初期設定 """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(f'''
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
      timestamp INTEGER PRIMARY KEY,
      size INTEGER,
      used INTEGER
    )
    ''')
    conn.close()


def load_data() -> pd.DataFrame:
    try:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query(f"""
                                SELECT * FROM (
                                    SELECT *
                                    FROM {TABLE_NAME}
                                    ORDER BY {INDEX_COL} DESC
                                    LIMIT {LIMIT_ROW}
                                ) AS sub
                                ORDER BY {INDEX_COL} ASC;
                               """,
                               conn,
                               index_col=["timestamp"],
                               parse_dates=["timestamp"])
        df.index += datetime.timedelta(hours=9)  # Asia/Tokyo location
        # timestamp化するときに強制的にUTC情報に変わっているため、loadしたときに
        # 書き換える必要がある
    except (sqlite3.DatabaseError, sqlite3.DataError) as e:
        print(e)
        raise e
    finally:
        conn.close()
    return df


async def save_data(interval: int):
    global df
    while True:
        await asyncio.sleep(interval)
        data = get_disk_space()
        print(data)

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute(f"INSERT INTO {TABLE_NAME} VALUES (?,?,?)", data)
        conn.commit()
        conn.close()


def get_disk_space() -> tuple[int, int, int]:
    """dfコマンドを打ってDisc容量を取得する"""
    output = subprocess.run(
        [
            "df",
            "-k",  # 1KiB blocks 単位で取得
            "--output=size,used",  # サイズと使用量のみ取得
            MNT_POINT,
        ],
        capture_output=True).stdout.decode()
    stats = output.split("\n")[1].split()  # ヘッダーを省略

    # UNIX timestampに変更
    timestamp = int(datetime.datetime.now().timestamp())
    # datetime.fromtimestamp(timestamp) で人間が見やすい時刻に変換
    # *1000してkB -> Byte表示
    size = int(stats[0].replace(",", "")) * 1000
    used = int(stats[1].replace(",", "")) * 1000
    return (timestamp, size, used)


def format_number(num):
    """Define a function to format the numbers"""
    suffixes = ['', 'k', 'M', 'G', 'T']
    for suffix in suffixes:
        if abs(num) < 1000:
            return f"{num:.2f}{suffix}"
        num /= 1000


def free_disc(df: pd.DataFrame) -> pd.DataFrame:
    """空き容量と使用率の表示"""
    last = df.iloc[-1:]
    last["free"] = last["size"] - last["used"]
    last["usage[%]"] = last["used"] / last["size"] * 100
    # 小数以下2桁に整形して人が見やすいk, M, G, Tに変換
    last = last.applymap(lambda x: format_number(x) if pd.notnull(x) else x)
    return last


def create_dash_app(df: pd.DataFrame,
                    requests_pathname_prefix: str = None) -> dash.Dash:
    """dash application run from main.py"""
    server = flask.Flask(__name__)
    server.secret_key = os.environ.get("secret_key", "secret")

    # To download
    # Bootstrap5 from https://getbootstrap.com/docs/5.2/getting-started/download/
    # then unzip it.
    # (this method is not use CDN instead LOCAL static file)
    external_stylesheets = [
        "/static/bootstrap-5.2.3-dist/css/bootstrap.min.css"
    ]
    app = dash.Dash(__name__,
                    server=server,
                    requests_pathname_prefix=requests_pathname_prefix,
                    external_stylesheets=external_stylesheets)

    # set to False by default.
    # When set to True, Dash will serve all scripts and style sheets locally
    app.scripts.config.serve_locally = True
    dcc._js_dist[0][
        "external_url"] = "https://cdn.plot.ly/plotly-basic-latest.min.js"

    # input_div = html.Div([
    # html.Span("臨界値:", id="label1", className="input-group-text"),
    #     dcc.Input(id="my-input",
    #               type="number",
    #               min=0,
    #               step=10,
    #               value=THRESHOLD,
    #               placeholder=THRESHOLD,
    #               className="form-control"),
    #     html.Span("kΩ", id="label2", className="input-group-text"),
    # ],
    #                    className = "input-group input-group-lg")
    app.layout = html.Div(
        [
            html.H1(TITLE),
            html.P(DESCRIPTION),
            # dcc.Dropdown(id="my-dropdown",
            #              options=[{
            #                  "label": "All",
            #                  "value": "All"
            #              }, {
            #                  "label": "Min",
            #                  "value": "Min"
            #              }, {
            #                  "label": "Candle",
            #                  "value": "Candle"
            #              }],
            #              value="All"),
            dcc.Graph(id="my-graph"),
            dcc.Interval(
                id="interval-component",
                interval=INTERVAL_SEC * 1000,  # millisecを指定する
                n_intervals=0),
            dash_table.DataTable(id="my-table",
                                 data=free_disc(df).to_dict("records")),
            # input_div,
        ],
        className="container")

    @app.callback(
        Output("my-graph", "figure"),
        [
            # 表示方法の変更
            # Input("my-dropdown", "value"),
            # 自動更新
            Input("interval-component", "n_intervals"),
            # 臨界値変更
            # Input("my-input", "value"),
            # グラフの表示範囲変更
            State("my-graph", "figure"),
            # Input("my-graph", "relayoutData"),
        ],
        prevent_initial_call=True,
    )
    def update_graph(
        selected_dropdown_value: str,
        n_intervals,
        # threshold: int,
        # current_figure,
        relayout_data=[],
    ):
        df = load_data()
        print(df.iloc[-10:])
        # ドロップダウンリストからグラフ種類の選択
        # dff, data = select_graph_type(df, selected_dropdown_value)

        # 臨界値エリアの表示
        # data.append(
        #     go.Scatter(
        #         x=dff.index,
        #         y=[threshold] * len(dff),
        #         name="臨界値",
        #         fill="tozeroy",
        #         mode="lines",
        #         line_color=THRESHOLD_COLOR,
        #         fillcolor=THRESHOLD_COLOR,
        #     ))

        show_df = df[-100:]  # [-MAX_POINT:]
        # (show_df.min().min(), show_df.max().max())
        show_range = (0, show_df.max().max() * 1.05)  # 5%シフト
        shift = datetime.timedelta(seconds=INTERVAL_SEC)

        layout = {
            "margin": {
                "l": 45,
                "r": 20,
                "b": 30,
                "t": 20,
            },
            "xaxis": {
                "range": (
                    # # 最大MAX_POINTポイントまで表示
                    show_df.index[-10] if len(df) > 10 else df.index[0],
                    # # 1秒先まで表示
                    show_df.index[-1] + shift,
                ),
                "rangeslider": {
                    "visible": False
                }
            },
            "yaxis": {
                "range": show_range,
                # "title": "size"
            },
        }

        data = [
            go.Scatter(
                x=df.index,
                y=df["size"],
                name="size",
                mode="lines",
            ),
            go.Scatter(
                x=df.index,
                y=df["used"],
                name="used",
                fill="tozeroy",
                mode="lines+markers",
            ),
        ]

        fig = {"data": data, "layout": layout}

        # assert isinstance(relayout_data, list)
        # relayout_dataでrangeが変えられていなければ、デフォルトのlayoutで返す
        items = [
            "xaxis.range[0]", "xaxis.range[1]", "yaxis.range[0]",
            "yaxis.range[1]"
        ]
        is_relayouted = any(item in relayout_data for item in items)
        if not is_relayouted:
            return fig

        # TODO
        # relayout_dataでrangeが変えられていれば、
        # ユーザーがグラフ尺度を変更したときにその状態をキープ
        fig["layout"]["xaxis"]["range"] = relayout_data.get("xaxis.range")
        fig["layout"]["yaxis"]["range"] = (df.min().min(), df.max().max())
        return fig

    return app
