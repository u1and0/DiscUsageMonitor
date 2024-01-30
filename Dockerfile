# karuwaza webのデータを集計、フィルタリング、ソートしてテーブルにまとめます
# usage:
#   docker run -it --rm -v `pwd`/data:/work/data -p 8880:8880 u1and0/omowazaweb
#
# data以下にpidmaster.csvという名前の品番マスタ一覧のCSVファイルが必要です。

# Python build container
FROM python:3.9.18-slim-bullseye as builder
WORKDIR /opt/app
RUN apt-get update &&\
    apt-get upgrade -y &&\
    apt-get install -y libfreetype6-dev \
                        libatlas-base-dev \
                        liblapack-dev
# For update image, rewrite below
#   -COPY requirements.lock /opt/app
#   +COPY requirements.txt /opt/app
# Then execute `docker exec -it container_name pip freeze > requirements.lock`
COPY requirements.txt /opt/app
RUN pip install --upgrade -r requirements.txt

# 実行コンテナ
FROM python:3.9.18-slim-bullseye as runner
WORKDIR /work
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

RUN useradd -r monitor_user
COPY main.py /usr/bin
COPY dashapp.py /usr/bin
RUN chmod -R +x /usr/bin/main.py

USER monitor_user
EXPOSE 8881
CMD ["python", "/usr/bin/main.py"]

LABEL maintainer="u1and0" \
      description="/mnt/zのディスク容量を記録、可視化" \
      version="u1and0/disk_usage_monitor:v0.1.1"
