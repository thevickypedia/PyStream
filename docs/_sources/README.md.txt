**Deployments**

[![book](https://github.com/thevickypedia/pystream/actions/workflows/pages/pages-build-deployment/badge.svg)][gha_pages]
[![pypi](https://github.com/thevickypedia/pystream/actions/workflows/python-publish.yml/badge.svg)][gha_pypi]

[![PyPI version shields.io](https://img.shields.io/pypi/v/stream-localhost)][pypi]
[![Pypi-format](https://img.shields.io/pypi/format/stream-localhost)](https://pypi.org/project/stream-localhost/#files)
[![Pypi-status](https://img.shields.io/pypi/status/stream-localhost)][pypi]

# Video Streaming
Python module to, stream videos via authenticated sessions using FastAPI

## Install
```shell
python -m pip install stream-localhost
```

## Usage
```python
import asyncio
import os
import pystream

if __name__ == '__main__':
    kwargs = dict(
        username="foo",
        password="bar",
        video_source=os.path.join(os.path.expanduser('~'), 'Downloads'),
    )
    # Add the following to host on local IP address, skip for localhost (127.0.0.1)
    # kwargs["video_host"] = pystream.utils.get_local_ip()
    asyncio.run(pystream.start(**kwargs))
```

### Env Variables
> :bulb: &nbsp; Environment variables can be loaded from any file. _Defaults to `.env`_<br>
> Set the env var `env_file` to the filename to use custom `.env` files

**Mandatory**
- **USERNAME**: Any username of choice.
- **PASSWORD**: Any password of choice.
- **VIDEO_SOURCE**: Source path for video files.
> :bulb: &nbsp; Files starting with `_` _(underscore)_ will be ignored

**Optional**
- **VIDEO_HOST**: IP address to host the video. Defaults to `127.0.0.1`
- **VIDEO_PORT**: Port number to host the application. Defaults to `8000`
- **FILE_FORMATS**: Sequence of supported video file formats. Defaults to `(.mp4, .mov)`
- **WORKERS**: Number of workers to spin up the `uvicorn` server. Defaults to `1`
- **WEBSITE**: Website to add to CORS configuration. _Required only if tunneled via CDN_
- **AUTO_THUMBNAIL**: Boolean flag to auto generate thumbnail images for preview. Defaults to `True`
- **SCAN_INTERVAL**: Interval in seconds to scan `VIDEO_SOURCE` in the background. Defaults traditional scan at run time.
- **NGROK_TOKEN**: Ngrok token to initiate tunneling via public endpoint.
> :bulb: &nbsp; When `SCAN_INTERVAL` is set to `None`, `VIDEO_SOURCE` will be scanned in real time whenever the user
> loads the landing page. Setting a `SCAN_INTERVAL` will scan the `VIDEO_SOURCE` in background and reduce runtime
> delays in case of complex directory structure.

## Coding Standards
Docstring format: [`Google`][google-docs] <br>
Styling conventions: [`PEP 8`][pep8] and [`isort`][isort]

## [Release Notes][release-notes]
**Requirement**
```shell
python -m pip install gitverse
```

**Usage**
```shell
gitverse-release reverse -f release_notes.rst -t 'Release Notes'
```

## Linting
`pre-commit` will ensure linting, run pytest, generate runbook & release notes, and validate hyperlinks in ALL
markdown files (including Wiki pages)

**Requirement**
```shell
pip install sphinx==5.1.1 pre-commit recommonmark
```

**Usage**
```shell
pre-commit run --all-files
```

## Pypi Package
[![pypi-module](https://img.shields.io/badge/Software%20Repository-pypi-1f425f.svg)][pypi-repo]

[https://pypi.org/project/stream-localhost/][pypi]

## Runbook
[![made-with-sphinx-doc](https://img.shields.io/badge/Code%20Docs-Sphinx-1f425f.svg)][sphinx]

[https://thevickypedia.github.io/pystream/][runbook]

## License & copyright

&copy; Vignesh Rao

Licensed under the [MIT License][license]

[license]: https://github.com/thevickypedia/pystream/blob/master/LICENSE
[pypi]: https://pypi.org/project/stream-localhost
[pypi-repo]: https://packaging.python.org/tutorials/packaging-projects/
[release-notes]: https://github.com/thevickypedia/pystream/blob/master/release_notes.rst
[gha_pages]: https://github.com/thevickypedia/pystream/actions/workflows/pages/pages-build-deployment
[gha_pypi]: https://github.com/thevickypedia/pystream/actions/workflows/python-publish.yml
[google-docs]: https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings
[pep8]: https://www.python.org/dev/peps/pep-0008/
[isort]: https://pycqa.github.io/isort/
[sphinx]: https://www.sphinx-doc.org/en/master/man/sphinx-autogen.html
[runbook]: https://thevickypedia.github.io/pystream/
