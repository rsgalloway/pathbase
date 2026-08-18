---
layout: default
title: Logs Example
description: Example service log storage templates for pathbase.
---

# Logs Example

This example models service log storage grouped by environment, service, date,
and level.

Example template:

```text
/var/log/{environment}/{service}/{date}/{level}.log
```

Example filepath:

```text
/var/log/prod/render-api/2026-07-26/error.log
```

Example env file:
[examples/logs/pathbase.env](https://github.com/rsgalloway/pathbase/blob/master/examples/logs/pathbase.env)

```bash
curl -L https://raw.githubusercontent.com/rsgalloway/pathbase/master/examples/logs/pathbase.env -o pathbase.env
```

Try it:

```bash
ENVPATH=./examples/logs/ pathbase parse \
  '/var/log/prod/render-api/2026-07-26/error.log'
```

Expected output:

```json
{
  "fields": {
    "date": "2026-07-26",
    "environment": "prod",
    "level": "error",
    "service": "render-api"
  },
  "template": "FILEPATH"
}
```
