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
