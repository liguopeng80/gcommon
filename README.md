# Common Python Libraries #

## About ##

"gcommon" is an python utility library for server and client
application development.

## install ##

```shell script
git clone https://github.com/liguopeng80/gcommon.git
pip install -e gcommon 
```

## usage ##

```

```


## History ##

The library was named "common" in 2008 and then renamed to "gcommon"
in 2010 to avoid name conflict. Its initial "g" comes from the
author's name (Guo Peng Li).

It was implemented on Pytohn 2.6 and then upgraded to Python 2.7,
while its all asynchronous functionalities were based on twisted.

On 2018, it was firstly migrated to Python 3 (3.6) but kept using
twsited as its aysnc infrastructure until 2021.

At the middle of 2021, most async functionalities in gcommon were
re-implemented with asycio and the library was published as MIT
license.
