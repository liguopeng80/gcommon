# Common Python Library #

## About ##

"gcommon" is a python utility library for server and client application development.

## Installing ##

```shell script
git clone https://github.com/liguopeng80/gcommon.git
pip install -e gcommon 
```

## Usage ##

### Usage for server application ###

```python
import asyncio

from gcommon.web import monkey_patch
monkey_patch.monkey_patch_flask()

from gcommon.aio.gserver import SimpleServer


class DemoServer(SimpleServer):
    SERVICE_NAME = 'demo'

    async def init_server(self):
        # parse configuration and init any dependencies to start service.
        # "init_server" can be async or not async. 
        """do whatever you want"""
        import demo_service

        self.logger.debug("init database...")
        demo_service.init_database(self.config)

        self.logger.debug("init demo service...")
        demo_service.init_service()

    def start_server(self):
        # "start_server" can be async or not async. 
        """do whatever you want"""
        from web.webapp import app

        host = self.config.get('service.web.host')
        port = self.config.get('service.web.port')
        auto_reload = self.config.get_bool('service.auto_reload')

        asyncio.create_task(app.run_task(host=host, port=port, use_reloader=auto_reload))
        self.logger.info("starting web service on %d...", port)


if __name__ == '__main__':
    DemoServer.start()
```

### Usage for client application ###

```python
from gcommon.utils.gglobal import Global
from gcommon.utils.gmain import init_main

# load configuration and init logger
Global.config = init_main()
```

### Usage for just utils ###

```python
from datetime import datetime
from gcommon.utils.gtime import DateUtil

last_monday = DateUtil.last_monday(datetime).now()
```

### Configuration

For server and client applications, gcommon will load configuration from "deploy/default.yaml" by default. 

```yaml
# deploy/default.yaml
service:
  web:
    base_url: /v3
    host: 0.0.0.0
    port: 12580
```
### Secret Configuration

You can also have a secret config file which will not be committed to git repository. 

```yaml
# deploy/secret.default.yaml
demo_postgre:
  server_address: "127.0.0.1"
  server_port: 5432

  username: "admin"
  password: "password"
```

How to load secret config:

```python
from gcommon.utils.gglobal import Global

db_config = Global.config.get("secret.demo_postgre")
password = db_config.password

password = Global.config.get("secret.demo_postgre.password")
```

## History ##

The library was named "common" in 2008 and then renamed to "gcommon" in 2010 to avoid name conflict. Its initial "g" comes from the author's name (Guo Peng Li).

It was implemented on Pytohn 2.6 and then upgraded to Python 2.7, while its all asynchronous functionalities were based on twisted.

On 2018, it was firstly migrated to Python 3 (3.6) but kept using twsited as its aysnc infrastructure until 2021.

At the middle of 2021, most async functionalities in gcommon were re-implemented with asycio and the library was published as MIT license.
