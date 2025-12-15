# Timestamp Queries Inside Passes

* Status: [Inactive](README.md#status-inactive)
* Issue: [#614](https://github.com/gpuweb/gpuweb/issues/614),
  [#2046](https://github.com/gpuweb/gpuweb/issues/2046)

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
