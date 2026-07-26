# Pathbase Examples

## Basic Formatting

```python
from pathbase import Template

template = Template(
    "{show}/{sequence}/{shot}/{step}/{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}"
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

print(path)
```

Expected output:

```text
bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.1001.exr
```

## Basic Parsing

```python
from pathbase import Template

template = Template(
    "{show}/{sequence}/{shot}/{step}/{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}"
)

fields = template.parse(
    "bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.1001.exr"
)

print(fields)
```

Expected output:

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

## Using `Template.from_env`

`pathbase` can read templates from `os.environ` without depending on envstack:

```python
import os

from pathbase import Template

os.environ["FILEPATH"] = (
    "${ROOT}/{show}/{sequence}/{shot}/{step}/"
    "{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}"
)
os.environ["ROOT"] = "/mnt/projects"

template = Template.from_env("FILEPATH")

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

print(path)
```

Expected output:

```text
/mnt/projects/bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.1001.exr
```

## Envstack Example

The repository includes a sample [pathbase.env](/mnt/homes/rsg/dev/pathbase/pathbase.env)
showing how template strings can be supplied from an envstack environment while
keeping `pathbase` itself dependency-free.

For the shared-defaults plus project-overrides pattern, see
[Overrides](overrides.md).
