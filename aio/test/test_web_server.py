# -*- coding: utf-8 -*-
# created: 2021-08-19
# creator: liguopeng@liguopeng.net

from quart import Quart, request, websocket

app = Quart(__name__)


@app.route("/")
@app.route("/", methods=["POST"])
async def hello():
    body = await request.get_data()
    return body


@app.websocket("/ws")
async def ws():
    while True:
        await websocket.send("hello")


app.run(host="127.0.0.1", port=12580)
