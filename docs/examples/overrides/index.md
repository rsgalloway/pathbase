---
layout: default
title: Overrides Example
description: Example shared and project-specific override templates for pathbase.
---

# Overrides Example

This folder demonstrates a shared `pathbase.env` plus a higher-priority
project-specific override.

- Shared env file: `examples/overrides/shared/pathbase.env`
- Big Buck Bunny override: `examples/overrides/bigbuckbunny/pathbase.env`

GitHub source:
- [examples/overrides/shared/pathbase.env](https://github.com/rsgalloway/pathbase/blob/master/examples/overrides/shared/pathbase.env)
- [examples/overrides/bigbuckbunny/pathbase.env](https://github.com/rsgalloway/pathbase/blob/master/examples/overrides/bigbuckbunny/pathbase.env)

```bash
curl -L https://raw.githubusercontent.com/rsgalloway/pathbase/master/examples/overrides/shared/pathbase.env -o shared.pathbase.env
curl -L https://raw.githubusercontent.com/rsgalloway/pathbase/master/examples/overrides/bigbuckbunny/pathbase.env -o bigbuckbunny.pathbase.env
```

Shared template example:

```text
/mnt/projects/{show}/{sequence}/{shot}/{step}/{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}
```

Override template example:

```text
/mnt/projects/bigbuckbunny/{sequence}/{shot}/tasks/{step}/{shot}_{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}
```

Example filepath:

```text
/mnt/projects/bigbuckbunny/seq001/shot010/tasks/lighting/shot010_render_beauty_v001.1001.exr
```

Try it from the `examples/overrides` directory so the project override has
priority over the shared config:

```bash
cd examples/overrides
ENVPATH=./bigbuckbunny:./shared pathbase parse \
  '/mnt/projects/bigbuckbunny/seq001/shot010/tasks/lighting/shot010_render_beauty_v001.1001.exr'
```

Expected output:

```json
{
  "fields": {
    "descriptor": "beauty",
    "frame": 1001,
    "sequence": "seq001",
    "shot": "shot010",
    "step": "lighting",
    "task": "render",
    "version": 1,
    "ext": "exr"
  },
  "template": "FILEPATH"
}
```
