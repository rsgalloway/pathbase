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

If you want the shortest Python API version of that flow, use
`Template.from_path(...)` and then parse through the returned template object.

```python
from pathbase import Template

path = "/mnt/projects/bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.1001.exr"

template = Template.from_path(path)
fields = template.parse(path)

print(template.template)
print(fields)
```

Expected output:

```text
${ROOT}/{show}/{sequence}/{shot}/{step}/{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}
```

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

Once you have the discovered template object, you can round-trip the parsed
fields back through it. For example, bump the version and format the next path:

```python
fields["version"] = fields["version"] + 1

next_path = template.format(**fields)
print(next_path)
```

Expected output:

```text
/mnt/projects/bigbuckbunny/seq001/shot010/lighting/render_beauty_v002.1001.exr
```

If you need the equivalent path for another platform and `envstack` is
installed, you can parse the source path once and ask `pathbase` to resolve the
target-platform template from the named envstack stack:

```python
from pathbase import Template

path = "/mnt/projects/bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.1001.exr"
template = Template.from_path(path)

windows_path = template.to_platform(path, "windows")

print(windows_path)
```

Expected output, assuming the `windows` platform resolves `ROOT=D:/projects`:

```text
D:/projects/bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.1001.exr
```

If `envstack` is not installed, you can still do the same conversion by passing
an explicit target environment mapping:

```python
from pathbase import Template

path = "/mnt/projects/bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.1001.exr"
template = Template.from_path(path)

windows_path = template.to_platform(
    path,
    "windows",
    target_env={
        "ROOT": "D:/projects",
        "FILEPATH": "${ROOT}/{show}/{sequence}/{shot}/{step}/{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}",
    },
)

print(windows_path)
```

If you also want the matched environment variable name, use
`match_template(...)`:

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

## Discovery Scope

`pathbase` matches against the resolved runtime environment, not only against a
`pathbase.env` file. That means templates can live in tool-local env files such
as `mytool.env`, `render.env`, or any other envstack-managed source, as long as
those variables are present in the environment seen by the Python process.

Auto-discovery is intentionally conservative:

- only string values that look like path templates are considered
- malformed candidate templates are skipped during discovery
- path separators are normalized during matching, so `/` and `\` do not break
  cross-platform parsing

If your process loads many template-like env vars and discovery becomes
ambiguous, pass a narrower `env=` mapping, use `Template.from_env(...)`, or
specify the template name explicitly.

## Frame Tokens: Numeric vs Flexible

When you use `{frame:04d}`, `pathbase` treats the field as numeric and returns
an integer when parsing a concrete file path.

```python
from pathbase import Template

template = Template(
    "${ROOT}/{show}/{sequence}/{shot}/{step}/"
    "{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}",
    env={"ROOT": "/mnt/projects"},
)

fields = template.parse(
    "/mnt/projects/bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.1001.exr"
)
print(fields["frame"])
print(type(fields["frame"]).__name__)
```

Expected output:

```text
1001
int
```

When you use `{frame}`, `pathbase` leaves the value flexible, which is useful
for frame-pad expressions such as `%08d`.

```python
from pathbase import Template

template = Template(
    "${ROOT}/{show}/{sequence}/{shot}/{step}/"
    "{task}_{descriptor}_v{version:03d}.{frame}.{ext}",
    env={"ROOT": "/mnt/projects"},
)

fields = template.parse(
    "/mnt/projects/bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.%08d.exr"
)
print(fields["frame"])
print(type(fields["frame"]).__name__)
```

Expected output:

```text
%08d
str
```

Choose based on the paths your tools need to parse:

- `{frame:04d}` for concrete frame files with numeric typing
- `{frame}` for flexible frame tokens, including frame pads like `%04d` and `%08d`

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

## Advanced: Current and Legacy Template Families

If your production has evolved over time, you can keep one current template and
one or more legacy variants side by side.

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
