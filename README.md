<img src="https://img.shields.io/badge/version-v0.1.1-FF7777.svg"></img>
<img src="https://img.shields.io/badge/LICENSE-MIT-3388FF.svg"></img>

ディスク Usage Monitor
=======

Save the data to a SQLite3 database by periodically hitting the df command,
visualize the data using plotly-dash.



## Usage

```
uvicorn --host "0.0.0.0" --port 8881 main:app /mnt/z
```

Open browser and access 'localhost:8881/index'

You can replace own port number 8881 to any number, replace own drive /dev/sda.
