**Deployments**

[![book][gha_pages_badge]][gha_pages]
[![pypi][gha_pypi_badge]][gha_pypi]
[![none-shall-pass][gha_none_shall_pass_badge]][gha_none_shall_pass]

[![PyPI version shields.io](https://img.shields.io/pypi/v/stream-localhost)][pypi]
[![Pypi-format](https://img.shields.io/pypi/format/stream-localhost)](https://pypi.org/project/stream-localhost/#files)
[![Pypi-status](https://img.shields.io/pypi/status/stream-localhost)][pypi]

# PyStream
Python module to, stream videos via authenticated sessions using FastAPI

## Install
```shell
python -m pip install stream-localhost
```

## Sample Usage
```python
import asyncio
import os
import pystream

if __name__ == '__main__':
    kwargs = dict(
        authorization={"Alan Turing": "Pr0gRamM1ng", "Linus Torvalds": "LinuxOS"},
        video_source=os.path.join(os.path.expanduser('~'), 'Downloads')
    )
    # Add the following to host on local IP address, skip for localhost (127.0.0.1)
    # kwargs["video_host"] = pystream.utils.get_local_ip()
    asyncio.run(pystream.start(**kwargs))
```

### Env Variables
> :bulb: &nbsp; Environment variables can _(optionally)_ be loaded from any plain text file.<br>
> Refer the [wiki page][wiki] for more information.

**Mandatory**
- **AUTHORIZATION**: Dictionary of key-value pairs with `username` as key and `password` as value.
- **VIDEO_SOURCE**: Source path for video files.
> :bulb: &nbsp; Files starting with `_` _(underscore)_ and `.` _(dot)_ will be ignored

**Optional**
- **VIDEO_HOST**: IP address to host the video. Defaults to `127.0.0.1`
- **VIDEO_PORT**: Port number to host the application. Defaults to `8000`
- **FILE_FORMATS**: Sequence of supported video file formats. Defaults to `(.mp4, .mov)`
- **WORKERS**: Number of workers to spin up the `uvicorn` server. Defaults to `1`
- **WEBSITE**: List of websites (_supports regex_) to add to CORS configuration. _Required only if tunneled via CDN_
- **AUTO_THUMBNAIL**: Boolean flag to auto generate thumbnail images for preview. Defaults to `True`

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
[gha_pages_badge]: https://github.com/thevickypedia/pystream/actions/workflows/pages/pages-build-deployment/badge.svg
[gha_pypi]: https://github.com/thevickypedia/pystream/actions/workflows/python-publish.yml
[gha_pypi_badge]: https://github.com/thevickypedia/pystream/actions/workflows/python-publish.yml/badge.svg
[gha_none_shall_pass]: https://github.com/thevickypedia/pystream/actions/workflows/markdown.yml
[gha_none_shall_pass_badge]: https://github.com/thevickypedia/pystream/actions/workflows/markdown.yml/badge.svg
[google-docs]: https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings
[pep8]: https://www.python.org/dev/peps/pep-0008/
[isort]: https://pycqa.github.io/isort/
[sphinx]: https://www.sphinx-doc.org/en/master/man/sphinx-autogen.html
[runbook]: https://thevickypedia.github.io/pystream/
[wiki]: https://github.com/thevickypedia/pystream/wiki
