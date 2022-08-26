# Timestamp Queries Inside Passes

**Roadmap:** This extension is **not under active consideration**, but may be considered later.
WebGPU implementations **must not** expose this functionality; doing so is a spec violation.
Note however, an implementation might provide an option (e.g. command line flag) to enable a draft
implementation, for developers who want to test this proposal or use its functionality for locally
profiling their application performance.

## WebGPU Spec Changes

**Feature flags:** `"timestamp-query-inside-passes"`

```
partial interface GPUComputePassEncoder {
    undefined writeTimestamp(GPUQuerySet querySet, GPUSize32 queryIndex);
};

partial interface GPURenderPassEncoder {
    undefined writeTimestamp(GPUQuerySet querySet, GPUSize32 queryIndex);
};
```

- `writeTimestamp(querySet, queryIndex)`:
    Writes a timestamp value into a `querySet` at index `queryIndex` when all previous commands have completed executing.
    - If the feature is not enabled, throws a `TypeError`.
    - `querySet`.`descriptor`.`type` must be `"timestamp"`.
    - `queryIndex` &lt; `querySet`.`descriptor`.`count`.
    - The query in `querySet` at index `queryIndex` has not been written earlier in a render pass.

## WGSL Spec Changes

**Enable directive(s):** N/A

## References

- <https://github.com/gpuweb/gpuweb/issues/614>
- <https://github.com/gpuweb/gpuweb/issues/2046>
