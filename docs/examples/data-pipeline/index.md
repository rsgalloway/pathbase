---
layout: default
title: Data Pipeline Example
description: Example partitioned dataset templates for pathbase.
---

# Data Pipeline Example

This example shows a partitioned data layout for datasets, dates, and shard
files.

Example template:

```text
/mnt/data/{dataset}/{date}/{partition}/part-{index:04d}.{ext}
```

Example filepath:

```text
/mnt/data/orders/2026-07-26/region-us-west/part-0007.parquet
```

Example env file:
[examples/data-pipeline/pathbase.env](https://github.com/rsgalloway/pathbase/blob/master/examples/data-pipeline/pathbase.env)

```bash
curl -L https://raw.githubusercontent.com/rsgalloway/pathbase/master/examples/data-pipeline/pathbase.env -o pathbase.env
```

Try it:

```bash
ENVPATH=./examples/data-pipeline/ pathbase parse \
  '/mnt/data/orders/2026-07-26/region-us-west/part-0007.parquet'
```

Expected output:

```json
{
  "fields": {
    "dataset": "orders",
    "date": "2026-07-26",
    "ext": "parquet",
    "index": 7,
    "partition": "region-us-west"
  },
  "template": "FILEPATH"
}
```
