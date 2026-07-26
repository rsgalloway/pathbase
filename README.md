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

Given a real filepath, `pathbase` can discover the matching template from
environment-provided templates and extract the tokens:

```bash
export FILEPATH='{show}/{sequence}/{shot}/{step}/{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}'
pathbase parse 'bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.1001.exr'
```

Expected output:

```json
{
  "fields": {
    "descriptor": "beauty",
    "ext": "exr",
    "frame": 1001,
    "sequence": "seq001",
    "shot": "shot010",
    "show": "bigbuckbunny",
    "step": "lighting",
    "task": "render",
    "version": 1
  },
  "template": "FILEPATH"
}
```

The same flow also works well with [envstack-managed templates](https://envstack.dev).
For example:

```bash
ENVPATH=./examples/vfx/ pathbase parse \
  '/mnt/projects/bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.1001.exr'
```

Expected output:

```json
{
  "fields": {
    "descriptor": "beauty",
    "ext": "exr",
    "frame": 1001,
    "sequence": "seq001",
    "shot": "shot010",
    "show": "bigbuckbunny",
    "step": "lighting",
    "task": "render",
    "version": 1
  },
  "template": "FILEPATH"
}
```

You can also work with templates directly from Python:

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

fields = template.parse(
    "bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.1001.exr"
)
```

Pathbase supports:

- `Template.format(...)` for path construction
- `Template.parse(path)` for field extraction
- automatic environment-based template discovery for CLI parsing and matching
- typed numeric fields such as `{version:03d}` and `{value:.2f}`
- repeated-field validation
- mixed-separator parsing
- embedded `$VAR` and `${VAR}` expansion from `os.environ` or an explicit mapping
- `Template.from_env(...)` as a convenience for environment-provided templates

Formatting output:

```text
bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.1001.exr
```

Parsing output:

```python
{
    "show": "bigbuckbunny",
    "sequence": "seq001",
    "shot": "shot010",
    "step": "lighting",
    "task": "render",
    "descriptor": "beauty",
    "version": 1,
    "frame": 1001,
    "ext": "exr",
}
```

## CLI

`pathbase` also includes a lightweight CLI:

```bash
pathbase format --template '{project}/{name}_v{version:03d}.txt' \
  project=demo name=report version=1

pathbase parse \
  'demo/report_v001.txt'

pathbase parse --template FILEPATH \
  'demo/report_v001.txt'

pathbase match 'demo/report.txt'
```

Additional documentation lives in [docs/README.md](docs/README.md):

- [Examples](docs/examples.md)
