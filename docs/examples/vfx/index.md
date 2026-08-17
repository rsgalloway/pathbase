---
layout: default
title: VFX Example
description: Example visual effects path templates for pathbase.
---

# VFX Example

This example models a common visual effects layout with show, sequence, shot,
step, and frame fields.

Example template:

```text
/mnt/projects/{show}/{sequence}/{shot}/{step}/{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}
```

Example filepath:

```text
/mnt/projects/bigbuckbunny/seq001/shot010/lighting/render_beauty_v001.1001.exr
```

Example env file:
[examples/vfx/pathbase.env](https://github.com/rsgalloway/pathbase/blob/master/examples/vfx/pathbase.env)

```bash
curl -L https://raw.githubusercontent.com/rsgalloway/pathbase/master/examples/vfx/pathbase.env -o pathbase.env
```

Try it:

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
