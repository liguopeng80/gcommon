# -*- coding: utf-8 -*- 
# created: 2021-06-23
# creator: liguopeng@liguopeng.net
import aiohttp


async def get(url, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, **kwargs) as response:
            return await response.json()


async def post(url, data, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, **kwargs) as response:
            return await response.json()


async def post_json(url, data, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, **kwargs) as response:
            return await response.json()


async def put(url, data, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.put(url, data=data, **kwargs) as response:
            return await response.json()


async def delete(url, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.delete(url, **kwargs) as response:
            return await response.json()

