import pathlib
import setuptools


# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()


# This call to setup() does all the work
setuptools.setup(
    name="gcommon",
    version="1.1.1",

    description="Common Pytohn Library for server and client application.",
    long_description=README,
    long_description_content_type="text/markdown",

    author="Guo Peng Li",
    author_email="liguopeng@liguopeng.net",
    url="https://github.com/liguopeng80/gcommon",

    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Topic :: Utilities",
        "Programming Language :: Python",
    ],

    packages=setuptools.find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    python_requires=">=3.7, <4",

    entry_points={
        'console_scripts': [
            'gcommon=gcommon.helpers:main',
        ],
    },

    install_requires = [
        "aiofiles==0.8.0",
        "aiohttp==3.8.1",
        "aiosignal==1.2.0",
        "async-timeout==4.0.2",
        "asyncpg==0.25.0",
        "attrs==21.4.0",
        "blinker==1.4",
        "certifi==2020.6.20",
        "cffi==1.15.0",
        "charset-normalizer==2.0.10",
        "click==8.0.3",
        "cryptography==36.0.1",
        "frozenlist==1.2.0",
        "greenlet==1.1.2",
        "h11==0.12.0",
        "h2==4.1.0",
        "hpack==4.0.0",
        "hypercorn==0.13.2",
        "hyperframe==6.0.1",
        "idna==3.3",
        "itsdangerous==2.0.1",
        "Jinja2==3.0.3",
        "MarkupSafe==2.0.1",
        "multidict==5.2.0",
        "priority==2.0.0",
        "pycparser==2.21",
        "pyOpenSSL==21.0.0",
        "python-dateutil==2.8.2",
        "pytz==2021.3",
        "PyYAML==6.0",
        "quart==0.16.2",
        "six==1.16.0",
        "SQLAlchemy==1.4.29",
        "toml==0.10.2",
        "Werkzeug==2.0.2",
        "wsproto==1.0.0",
        "yarl==1.7.2",
    ],
)
