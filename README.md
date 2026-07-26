# pathbase

[![PyPI](https://img.shields.io/pypi/v/pathbase.svg?color=blue)](https://pypi.org/project/pathbase/)
[![CI](https://github.com/rsgalloway/pathbase/actions/workflows/tests.yml/badge.svg)](https://github.com/rsgalloway/pathbase/actions/workflows/tests.yml)
[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](LICENSE)

`pathbase` is a lightweight, dependency-free Python library for bidirectional
filesystem path templates.

It is being extracted from the path-template functionality in `envstack.path`
into a focused standalone package that stays intentionally small.

## Installation

```bash
pip install -U pathbase
```

## Status

This repository now includes the first functional extraction slice:

- `Template.format(...)` for path construction
- `Template.parse(...)` for field extraction
- typed numeric fields such as `{version:03d}` and `{value:.2f}`
- repeated-field validation
- mixed-separator parsing for POSIX and Windows-style paths
- embedded `$VAR` and `${VAR}` expansion from `os.environ` or an explicit mapping

Envstack-specific stack loading is intentionally not part of the core package.

## Quick Example

```python
from pathbase import Template

template = Template(
    "/shows/{show}/shots/{sequence}/{shot}/"
    "{shot}_{task}_v{version:03d}.{frame:04d}.exr"
)

path = template.format(
    show="bigbuckbunny",
    sequence="seq001",
    shot="0150",
    task="plate",
    version=1,
    frame=1001,
)

print(path)
```

Expected output:

```text
/shows/bigbuckbunny/shots/seq001/0150/0150_plate_v001.1001.exr
```

Parsing works in the other direction:

```python
fields = template.parse("/shows/bigbuckbunny/shots/seq001/0150/0150_plate_v001.1001.exr")

print(fields)
```

Expected output:

```python
{
    "show": "bigbuckbunny",
    "sequence": "seq001",
    "shot": "0150",
    "task": "plate",
    "version": 1,
    "frame": 1001,
}
```

## Embedded Environment Variables

Templates may contain embedded environment variables:

```python
from pathbase import Template

template = Template("${ROOT}/{show}/{shot}.exr", env={"ROOT": "/mnt/projects"})
path = template.format(show="bigbuckbunny", shot="0150")
```

`Template.from_env("PLATE_FILE")` is also supported and reads from `os.environ`
by default.

## Compatibility Notes

The preferred API is:

- `Template.format(...)`
- `Template.parse(path)`
- `Template.fields`
- `Template.formats`
