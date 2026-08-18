---
layout: default
title: Pathbase Docs
description: Overview and quick-start examples for pathbase path templates.
---

# Pathbase Docs

`pathbase` is a lightweight Python library for formatting paths, parsing paths
back into tokens, and automatically discovering which template a real filepath
matches.

## Quick Example

Given a real filepath, `pathbase` can discover the matching template from
environment-provided templates and extract the tokens:

This example assumes [envstack](https://envstack.dev) is installed so
`ENVPATH` is resolved before `pathbase` runs.

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

With [envstack-managed templates](https://envstack.dev), you can also emit the
equivalent path for another platform:

```bash
ENVPATH=./examples/vfx/ pathbase parse --platform windows \
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
  "platform_path": "D:/projects/bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.1001.exr",
  "template": "FILEPATH"
}
```

If `envstack` is not installed, `pathbase` still supports direct environment
variables and explicit mappings from Python.

You can also work with templates directly from Python:

```python
from pathbase import Template

template = Template(
    "${ROOT}/{show}/{sequence}/{shot}/{step}/"
    "{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}"
    ,
    env={"ROOT": "/mnt/projects"},
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
    "/mnt/projects/bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.1001.exr"
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
/mnt/projects/bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.1001.exr
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
ROOT=/mnt/projects pathbase format --template '${ROOT}/{project}/{name}_v{version:03d}.txt' \
  project=demo name=report version=1

ENVPATH=./examples/vfx/ pathbase parse \
  '/mnt/projects/bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.1001.exr'

ENVPATH=./examples/vfx/ pathbase parse --platform windows \
  '/mnt/projects/bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.1001.exr'

pathbase parse \
  '/mnt/projects/demo/report_v001.txt'

pathbase parse --template FILEPATH \
  '/mnt/projects/demo/report_v001.txt'

pathbase match '/mnt/projects/demo/report.txt'
```
