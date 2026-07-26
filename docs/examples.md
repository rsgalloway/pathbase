# Pathbase Examples

## Parse a Filepath Without Knowing the Template

If environment variables contain template strings, `pathbase` can discover the
matching template automatically from a concrete filepath.

```bash
export FILEPATH='{project}/{name}_v{version:03d}.txt'
pathbase parse 'demo/report_v001.txt'
```

Expected output:

```json
{
  "fields": {
    "name": "report",
    "project": "demo",
    "version": 1
  },
  "template": "FILEPATH"
}
```

This is useful when the caller has a real path and wants the extracted tokens
without manually specifying the template name.

## Parse a Filepath Using `ENVPATH`

If you are using envstack, you can point `ENVPATH` at one of the example env
directories and let envstack provide the template values to `pathbase`:

```bash
export ENVPATH=./examples/vfx
pathbase parse \
  '/mnt/projects/bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.1001.exr'
```

This keeps the template definitions outside the shell command itself while still
letting `pathbase` discover the matching template from the environment.

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

The repository includes a generic sample [pathbase.env](../pathbase.env)
and several domain-specific env examples under
[examples/README.md](../examples/README.md), showing
how template strings can be supplied from environment configuration while
keeping `pathbase` itself dependency-free.

For the shared-defaults plus project-overrides pattern, see
[Overrides](overrides.md).

For `distman` target selection and deployment examples, including selecting an
example flavor while always deploying to the same `pathbase.env` destination, see
[Distribution](distribution.md).

## CLI Examples

The `pathbase` CLI provides a thin wrapper around the same template operations.

Format a path from fields:

```bash
pathbase format --template '{project}/{name}_v{version:03d}.txt' \
  project=demo name=report version=1
```

Expected output:

```text
demo/report_v001.txt
```

Parse a path back into fields:

```bash
export FILEPATH='{project}/{name}_v{version:03d}.txt'
pathbase parse \
  'demo/report_v001.txt'
```

Expected output:

```json
{
  "fields": {
    "name": "report",
    "project": "demo",
    "version": 1
  },
  "template": "FILEPATH"
}
```

Use a specific env var name when more than one template may exist:

```bash
pathbase parse --template FILEPATH 'demo/report_v001.txt'
```

Test whether a path matches a template:

```bash
export FILEPATH='{project}/{name}.txt'
pathbase match 'demo/report.txt'
```

Expected output:

```text
FILEPATH
```
