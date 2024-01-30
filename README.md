<img src="https://img.shields.io/badge/version-v0.1.0-FF7777.svg"></img>
<img src="https://img.shields.io/badge/LICENSE-MIT-3388FF.svg"></img>

Disc Usage Monitor
=======

Save the data to a SQLite3 database by periodically hitting the df command,
visualize the data using plotly-dash.



## Usage

```
uvicorn --host "0.0.0.0" --port 8881 main:app
```

Open browser and access 'localhost:8881/index'
