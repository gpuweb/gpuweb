# Pipeline Statistics Queries

**Roadmap:** This draft extension is **not on the standards track**. It is currently intended to be used only in non-Web-compliant contexts, such as by Web developers who enable a command line flag or other non-default option in order to profile the performance of their application.

**GPUFeatureName(s):** `"pipeline-statistics-query"`

## WebGPU Spec Changes

```
partial dictionary GPUQuerySetDescriptor {
    sequence<GPUPipelineStatisticName> pipelineStatistics = [];
};

enum GPUPipelineStatisticName {
    "vertex-shader-invocations",
    "clipper-invocations",
    "clipper-primitives-out",
    "fragment-shader-invocations",
    "compute-shader-invocations",
};

partial interface GPUComputePassEncoder {
    undefined beginPipelineStatisticsQuery(GPUQuerySet querySet, GPUSize32 queryIndex);
    undefined endPipelineStatisticsQuery();
};

partial interface GPURenderPassEncoder {
    undefined beginPipelineStatisticsQuery(GPUQuerySet querySet, GPUSize32 queryIndex);
    undefined endPipelineStatisticsQuery();
};
```

- `GPUQuerySetDescriptor.pipelineStatistics`:
    The set of `GPUPipelineStatisticName` values in this sequence defines which pipeline statistics will be returned in the new query set.
    - Must be empty if the query set type is not `"pipeline-statistics"`.
    - Must not contain duplicate entries.
- `beginPipelineStatisticsQuery(querySet, queryIndex)`:
    Begins recording pipeline statistics to write into `querySet` at index `queryIndex`.
    - If the feature is not enabled, throws a `TypeError`.
    - Fails if a pipeline statistics query is already open.
- `endPipelineStatisticsQuery()`:
    Ends recording the current pipeline statistics query.
    - If the feature is not enabled, throws a `TypeError`.
    - Fails if a pipeline statistics query is not open.
- In `createQuerySet()`:
    - If the query set type is `"pipeline-statistics"` but the feature is not enabled, throws a `TypeError`.
- In `resolveQuerySet()`:
    When resolving a pipeline statistics query, each result is written as a `GPUSize64`, and the number and order of the results written to GPU buffer matches the number and order of `GPUPipelineStatisticName`s specified in `GPUQuerySetDescriptor.pipelineStatistics`.

## WGSL Spec Changes

None.

## References

- <https://github.com/gpuweb/gpuweb/issues/614>
- <https://github.com/gpuweb/gpuweb/issues/794>
