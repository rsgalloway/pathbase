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

## Quick Example

```python
from pathbase import Template

template = Template(
    "{show}/{sequence}/{shot}/{step}/"
    "{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}"
)

path = template.format(
    show="bigbuckbunny",
    sequence="seq001",
    shot="shot010",
    step="lighting",
    task="render",
    descriptor="beauty",
    version=1,
    frame=1001,
    ext="exr",
)
```

Pathbase supports:

- `Template.format(...)` for path construction
- `Template.parse(path)` for field extraction
- typed numeric fields such as `{version:03d}` and `{value:.2f}`
- repeated-field validation
- mixed-separator parsing
- embedded `$VAR` and `${VAR}` expansion from `os.environ` or an explicit mapping
- `Template.from_env(...)` as a convenience for environment-provided templates

Additional documentation lives in [docs/README.md](docs/README.md):

- [Examples](docs/examples.md)
