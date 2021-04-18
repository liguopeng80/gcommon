# -*- coding: utf-8 -*- 
# created: 2013-05-25
# creator: liguopeng@liguopeng.net

import requests


def download_file(url, target_file):
    r = requests.get(url)
    with open(target_file, "wb") as file:
        file.write(r.content)
