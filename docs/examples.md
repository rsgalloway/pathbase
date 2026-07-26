# Pathbase Examples

## Example Flavors

For concrete, domain-specific `pathbase.env` examples, see:

- [Examples Overview](/examples/README.md)
- [VFX](/examples/vfx/README.md)
- [Animation](/examples/animation/README.md)
- [Data Pipeline](/examples/data-pipeline/README.md)
- [Logs](/examples/logs/README.md)
- [ML Artifacts](/examples/ml-artifacts/README.md)
- [Overrides](/examples/overrides/README.md)

## Parse a Filepath Without Knowing the Template

If environment variables contain template strings, `pathbase` can discover the
matching template automatically from a concrete filepath.

```bash
export FILEPATH='${ROOT}/{project}/{name}_v{version:03d}.txt'
export ROOT='/mnt/projects'
pathbase parse '/mnt/projects/demo/report_v001.txt'
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

The same auto-discovery model is available in Python API integrations via
`match_template(path, env=...)` and `Template.from_path(path, env=...)`. See
[API](api.md) for examples.

## Parse a Filepath Using `ENVPATH`

If you are using [envstack](https://envstack.dev), you can point `ENVPATH` at one
of the example env directories and let envstack provide the template values to
`pathbase`:

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

This keeps the template definitions outside the shell command itself while still
letting `pathbase` discover the matching template from the environment.

## Parse Current and Legacy Template Variants

`pathbase parse PATH` does not require the caller to know whether a path matches
the current template or a legacy variant. If your environment contains
`FILEPATH`, `FILEPATH_V1`, and `FILEPATH_V2`, path discovery will try all of
them and return the matching template name.

Example environment:

```bash
export FILEPATH='${ROOT}/{show}/{sequence}/{shot}/{step}/{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}'
export FILEPATH_V1='${ROOT}/{show}/{sequence}/{shot}/{task}/{task}_{descriptor}.{frame:04d}.{ext}'
export FILEPATH_V2='${ROOT}/{show}/{sequence}/{shot}/{step}/{task}_{descriptor}_f{frame:04d}.{ext}'
export ROOT='/mnt/projects'
```

Current filepath:

```bash
pathbase parse '/mnt/projects/bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.1001.exr'
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

Legacy `V1` filepath:

```bash
pathbase parse '/mnt/projects/bigbuckbunny/seq001/shot010/render/render_beauty.1001.exr'
```

This path does not require `--template FILEPATH_V1`. `pathbase` discovers that
it matches `FILEPATH_V1` automatically.

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
    "task": "render"
  },
  "template": "FILEPATH_V1"
}
```

Equivalent Python API flow:

```python
from pathbase import match_template

env = {
    "ROOT": "/mnt/projects",
    "FILEPATH": "${ROOT}/{show}/{sequence}/{shot}/{step}/{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}",
    "FILEPATH_V1": "${ROOT}/{show}/{sequence}/{shot}/{task}/{task}_{descriptor}.{frame:04d}.{ext}",
    "FILEPATH_V2": "${ROOT}/{show}/{sequence}/{shot}/{step}/{task}_{descriptor}_f{frame:04d}.{ext}",
}

path = "/mnt/projects/bigbuckbunny/seq001/shot010/render/render_beauty.1001.exr"
template_name, template = match_template(path, env=env)

print(template_name)
print(template.parse(path))
```

Expected output:

```text
FILEPATH_V1
```

```python
{
    "show": "bigbuckbunny",
    "sequence": "seq001",
    "shot": "shot010",
    "task": "render",
    "descriptor": "beauty",
    "frame": 1001,
    "ext": "exr",
}
```

Legacy `V2` filepath:

```bash
pathbase parse '/mnt/projects/bigbuckbunny/seq001/shot010/lighting/render_beauty_f1001.exr'
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
    "task": "render"
  },
  "template": "FILEPATH_V2"
}
```

This is already supported today as long as the template shapes are distinct. If
more than one template matches the same path shape, `pathbase` reports that
ambiguity explicitly rather than guessing.

## Basic Formatting

```python
from pathbase import Template

template = Template(
    "/mnt/projects/{show}/{sequence}/{shot}/{step}/{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}"
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
/mnt/projects/bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.1001.exr
```

## Basic Parsing

```python
from pathbase import Template

template = Template(
    "/mnt/projects/{show}/{sequence}/{shot}/{step}/{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}"
)

fields = template.parse(
    "/mnt/projects/bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.1001.exr"
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

The repository includes several domain-specific env examples under
[examples/README.md](../examples/README.md), showing how template strings can
be supplied from environment configuration while keeping `pathbase` itself
dependency-free.

For the shared-defaults plus project-overrides pattern, see
[Overrides](overrides.md).

For `distman` target selection and deployment examples, including selecting an
example flavor while always deploying to the same `pathbase.env` destination, see
[Distribution](distribution.md).

## CLI Examples

The `pathbase` CLI provides a thin wrapper around the same template operations.

Format a path from fields:

```bash
pathbase format --template '${ROOT}/{project}/{name}_v{version:03d}.txt' \
  ROOT=/mnt/projects project=demo name=report version=1
```

Expected output:

```text
/mnt/projects/demo/report_v001.txt
```

Parse a path back into fields:

```bash
export FILEPATH='${ROOT}/{project}/{name}_v{version:03d}.txt'
export ROOT='/mnt/projects'
pathbase parse \
  '/mnt/projects/demo/report_v001.txt'
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
pathbase parse --template FILEPATH '/mnt/projects/demo/report_v001.txt'
```

Test whether a path matches a template:

```bash
export FILEPATH='${ROOT}/{project}/{name}.txt'
export ROOT='/mnt/projects'
pathbase match '/mnt/projects/demo/report.txt'
```

Expected output:

```text
FILEPATH
```
