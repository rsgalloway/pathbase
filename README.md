# pathbase

`pathbase` is a lightweight, dependency-free Python library for bidirectional
filesystem path templates.

## Status

This repository is currently a minimal v0 scaffold.

## Planned Direction

The core idea is a single template that can both format and parse paths:

```python
from pathbase import Template

template = Template(
    "/shows/{show}/shots/{sequence}/{shot}/"
    "{shot}_{task}_v{version:03d}.{frame:04d}.exr"
)

path = template.apply_fields(
    show="bigbuckbunny",
    sequence="bbb",
    shot="0150",
    task="plate",
    version=1,
    frame=1001,
)

fields = template.parse(path)
```

Pathbase is intended to remain focused on path formatting and parsing rather
than environment loading, filesystem mutation, or pipeline orchestration.

## Installation

```bash
pip install -U pathbase
```
