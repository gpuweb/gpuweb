# Pipeline Statistics Queries

**Roadmap:** This extension is **not under active consideration**, but may be considered later.
WebGPU implementations **must not** expose this functionality; doing so is a spec violation.
Note however, an implementation might provide an option (e.g. command line flag) to enable a draft
implementation, for developers who want to test this proposal or use its functionality for locally
profiling their application performance.

## WebGPU Spec Changes

**Feature flags:** `"pipeline-statistics-query"`

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
    - Fails if the pass is not open.
- In `createQuerySet()`:
    - If the query set type is `"pipeline-statistics"` but the feature is not enabled, throws a `TypeError`.
- In `resolveQuerySet()`:
    When resolving a pipeline statistics query, each result is written as a `GPUSize64`, and the number and order of the results written to GPU buffer matches the number and order of `GPUPipelineStatisticName`s specified in `GPUQuerySetDescriptor.pipelineStatistics`.
- In `GPUComputePassEncoder`/`GPURenderPassEncoder`.`end()`:
    - Fails if a pipeline statistics query is still open.

## WGSL Spec Changes

**Enable directive(s):** N/A

## References

- <https://github.com/gpuweb/gpuweb/issues/614>
- <https://github.com/gpuweb/gpuweb/issues/794>
