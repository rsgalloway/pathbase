# Pathbase API

This guide focuses on the Python API surface that is most useful when
integrating `pathbase` into tools, launchers, and pipeline code.

## Core Imports

```python
from pathbase import Template, find_matching_templates, match_template
```

## Parse a Path Without Knowing the Template

This is the most important integration pattern for many tools: start with a
real filepath, let `pathbase` discover the matching template automatically, and
get the parsed fields back.

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
fields = template.parse(path)

print(template_name)
print(fields)
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

This does not require the caller to preselect `FILEPATH_V1`. The path is
matched automatically against all available templates in the environment.

## Build a Template From a Path and Parse It

If you want a `Template` object first and then want to inspect or parse through
that object, use `Template.from_path(...)`.

```python
from pathbase import Template, match_template

env = {
    "ROOT": "/mnt/projects",
    "FILEPATH": "${ROOT}/{show}/{sequence}/{shot}/{step}/{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}",
    "FILEPATH_V1": "${ROOT}/{show}/{sequence}/{shot}/{task}/{task}_{descriptor}.{frame:04d}.{ext}",
    "FILEPATH_V2": "${ROOT}/{show}/{sequence}/{shot}/{step}/{task}_{descriptor}_f{frame:04d}.{ext}",
}

path = "/mnt/projects/bigbuckbunny/seq001/shot010/lighting/render_beauty_f1001.exr"

template_name, _ = match_template(path, env=env)
template = Template.from_path(path, env=env)

print(template_name)
print(template.template)
print(template.parse(path))
```

Expected output:

```text
FILEPATH_V2
```

```text
${ROOT}/{show}/{sequence}/{shot}/{step}/{task}_{descriptor}_f{frame:04d}.{ext}
```

```python
{
    "show": "bigbuckbunny",
    "sequence": "seq001",
    "shot": "shot010",
    "step": "lighting",
    "task": "render",
    "descriptor": "beauty",
    "frame": 1001,
    "ext": "exr",
}
```

## Format a Path

Use `Template.format(...)` when your tool already knows which template it wants
to write.

```python
from pathbase import Template

template = Template(
    "${ROOT}/{show}/{sequence}/{shot}/{step}/"
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
    ROOT="/mnt/projects",
)

print(path)
```

Expected output:

```text
/mnt/projects/bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.1001.exr
```

## Parse a Path

Use `Template.parse(path)` when the template is already known and you want the
fields back.

```python
from pathbase import Template

template = Template(
    "${ROOT}/{show}/{sequence}/{shot}/{step}/"
    "{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}"
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

## Read a Template From the Environment

Use `Template.from_env(...)` when your integration reads template strings from
environment variables.

```python
import os

from pathbase import Template

os.environ["FILEPATH"] = (
    "${ROOT}/{show}/{sequence}/{shot}/{step}/"
    "{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}"
)
os.environ["ROOT"] = "/mnt/projects"

template = Template.from_env("FILEPATH")
print(template.format(
    show="bigbuckbunny",
    sequence="seq001",
    shot="shot010",
    step="lighting",
    task="render",
    descriptor="beauty",
    version=1,
    frame=1001,
    ext="exr",
))
```

## Discover the Matching Template for a Path

Use `match_template(path, env=...)` when your tool has a real filepath and
needs to know which environment template it belongs to.

```python
from pathbase import match_template

env = {
    "ROOT": "/mnt/projects",
    "FILEPATH": "${ROOT}/{show}/{sequence}/{shot}/{step}/{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}",
    "FILEPATH_V1": "${ROOT}/{show}/{sequence}/{shot}/{task}/{task}_{descriptor}.{frame:04d}.{ext}",
    "FILEPATH_V2": "${ROOT}/{show}/{sequence}/{shot}/{step}/{task}_{descriptor}_f{frame:04d}.{ext}",
}

name, template = match_template(
    "/mnt/projects/bigbuckbunny/seq001/shot010/render/render_beauty.1001.exr",
    env=env,
)

print(name)
print(template.parse("/mnt/projects/bigbuckbunny/seq001/shot010/render/render_beauty.1001.exr"))
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

## Build a Template Directly From a Path

Use `Template.from_path(...)` when you want the matching `Template` object
first and then want to parse or inspect it.

```python
from pathbase import Template

env = {
    "ROOT": "/mnt/projects",
    "FILEPATH": "${ROOT}/{project}/{name}_v{version:03d}.txt",
    "FILEPATH_V1": "${ROOT}/{project}/{name}.{ext}",
}

template = Template.from_path("/mnt/projects/demo/report_v001.txt", env=env)
print(template.template)
print(template.parse("/mnt/projects/demo/report_v001.txt"))
```

Expected output:

```text
${ROOT}/{project}/{name}_v{version:03d}.txt
```

```python
{
    "project": "demo",
    "name": "report",
    "version": 1,
}
```

## Inspect Multiple Possible Matches

Use `find_matching_templates(...)` when you want to detect and handle ambiguity
 yourself.

```python
from pathbase import find_matching_templates

env = {
    "ROOT": "/mnt/projects",
    "FILEPATH": "${ROOT}/{project}/{name}.txt",
    "ALT_FILEPATH": "${ROOT}/{project}/{artifact}.txt",
}

matches = find_matching_templates("/mnt/projects/demo/report.txt", env=env)
print([name for name, _template in matches])
```

Expected output:

```python
["FILEPATH", "ALT_FILEPATH"]
```

## Path-Like Inputs

`Template`, `Template.parse(...)`, `match_template(...)`, and
`Template.from_path(...)` accept path-like values, not just plain strings.

```python
from pathlib import Path

from pathbase import Template

template = Template("${ROOT}/{project}/{name}.txt", env={"ROOT": "/mnt/projects"})
fields = template.parse(Path("/mnt/projects/demo/report.txt"))
print(fields)
```

Expected output:

```python
{
    "project": "demo",
    "name": "report",
}
```
