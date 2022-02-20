#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2016-01-18

import aiohttp

Content_Type_XML = "application/xml"
Content_Type_Plain_Text = "text/plain"
Content_Type_JSON = "application/json"
Content_Type_URL_Encoded = "application/x-www-form-urlencoded; charset=UTF-8"


class Session(object):
    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def get(self, url, **kwargs):
        async with self.session.get(url, **kwargs) as response:
            return await response.text()

    async def post(self, url, data, **kwargs):
        async with self.session.post(url, data=data, **kwargs) as response:
            return await response.text()

    async def post_json(self, url, data, **kwargs):
        async with self.session.post(url, json=data, **kwargs) as response:
            return await response.text()

    async def put(self, url, data, **kwargs):
        async with self.session.put(url, data=data, **kwargs) as response:
            return await response.text()

    async def delete(self, url, **kwargs):
        async with self.session.delete(url, **kwargs) as response:
            return await response.text()
