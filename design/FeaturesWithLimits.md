# Features that add new limits

Some new features add associated limits. This document records a design policy for such features.

## Common behaviors

- `{ newLimit: undefined }` is allowed even if `newLimit` is unknown. (It has no effect.)
- Limits entries associated with features have these Adapter Capability Guarantees:
  - If the feature is available, its limits are `better` than or equal to the default.
  - If not, its limits are `undefined`.
  - They are `undefined` if the feature is unavailable on the adapter.
- It is allowed to request a limit that's available on the adapter (that is,
  not `undefined` in `adapter.limits`), even without also requesting the corresponding feature.
  It won't have any effect, but the limit request will still be validated against the adapter.
- It is allowed to request a feature that's available on the adapter, even without also
  requesting the corresponding limit(s). (They will get their default values.)

## Policies for new features

- There should be a feature name for each such feature - don't just add a new limit
  (defaulting to 0) on its own.
  - Allows us to clearly guarantee a default value for the limit when the feature is available.
    (You only have to request the feature, not figure out what limit you need to request.)
  - Is consistent with features that add 0 limits or more than 1 limit.
- Each new limit should define its "default" value as the default non-trivial value
  (that is, ignoring whether the feature is available/requested).

## Example

The new feature is `"foo"`.
The new limit is `maxFoo`, and it has a default value of `5`.

### Case Studies

For each case study we'll look at how a piece of code behaves in several cases given an adapter `a`:

- *Available (5)*: a browser which implements `"foo"`, on a device with support with `maxFoo: 5`.
  - `a.features.has("foo")` is `true`
  - `'maxFoo' in a.limits` is `true`
  - `a.limits.maxFoo` is `7`
- *Available (7)*: a browser which implements `"foo"`, on a device with support with `maxFoo: 7`.
  - `a.features.has("foo")` is `true`
  - `'maxFoo' in a.limits` is `true`
  - `a.limits.maxFoo` is `7`
- *Unavailable*: a browser which implements `"foo"`, on a device without support.
  - `a.features.has("foo")` is `false`
  - `'maxFoo' in a.limits` is `true`
  - `a.limits.maxFoo` is `undefined`
- *Unimplemented*: a browser which hasn't implemented `"foo"` **but does implement the new rules allowing unknown limits set to `undefined`**
  - `a.features.has("foo")` is `false`
  - `'maxFoo' in a.limits` is `false`
  - `a.limits.maxFoo` is `undefined`

In all cases `requiredFeatures: []` is the same as not specifying it,
`requiredLimits: {}` is the same as not specifying it, and
`maxFoo: undefined` is the same as not specifying it.
We'll ignore the `requiredLimits: a.limits` case, as it should be equivalent to one of the other cases
(which one depends on the resolution of [#4277](https://github.com/gpuweb/gpuweb/issues/4277)).

- `a.requestDevice({ requiredFeatures:         [], requiredLimits: { maxFoo:       undefined } })`
  - *Available (7)*: OK, request ignored, device limit is `undefined`
  - *Available (5)*: OK, request ignored, device limit is `undefined`
  - *Unavailable*:   OK, request ignored, device limit is `undefined`
  - *Unimplemented*: OK, request ignored, device limit is `undefined`
- `a.requestDevice({ requiredFeatures:         [], requiredLimits: { maxFoo: a.limits.maxFoo } })`
  - *Available (7)*: OK, device limit is `undefined` (request has no effect)
  - *Available (5)*: OK, device limit is `undefined` (request has no effect)
  - *Unavailable*:   OK (limit request ignored because undefined)
  - *Unimplemented*: OK (limit request ignored because undefined)
- `a.requestDevice({ requiredFeatures:         [], requiredLimits: { maxFoo:               5 } })`
  - *Available (7)*: OK, device limit is `undefined` (request has no effect)
  - *Available (5)*: OK, device limit is `undefined` (request has no effect)
  - *Unavailable*:   error, limit key not available
  - *Unimplemented*: error, limit key not available
- `a.requestDevice({ requiredFeatures:         [], requiredLimits: { maxFoo:               7 } })`
  - *Available (7)*: OK, device limit is `undefined` (request has no effect)
  - *Available (5)*: error, limit value not available (even though request would have no effect)
  - *Unavailable*:   error, limit key not available
  - *Unimplemented*: error, limit key not available
- `a.requestDevice({ requiredFeatures:    ["foo"], requiredLimits: { maxFoo:       undefined } })`
  - *Available (7)*: OK, enabled with limit set to default (5)
  - *Available (5)*: OK, enabled with limit set to default (5)
  - *Unavailable*:   error, feature not available
  - *Unimplemented*: error, feature not available
- `a.requestDevice({ requiredFeatures:    ["foo"], requiredLimits: { maxFoo: a.limits.maxFoo } })`
  - *Available (7)*: OK, enabled with limit set to 7
  - *Available (5)*: OK, enabled with limit set to 5
  - *Unavailable*:   error, feature not available
  - *Unimplemented*: error, feature not available
- `a.requestDevice({ requiredFeatures:    ["foo"], requiredLimits: { maxFoo:               5 } })`
  - *Available (7)*: OK, enabled with limit set to 5
  - *Available (5)*: OK, enabled with limit set to 5
  - *Unavailable*:   error, feature not available, limit key not available
  - *Unimplemented*: error, feature not available, limit key not available
- `a.requestDevice({ requiredFeatures:    ["foo"], requiredLimits: { maxFoo:               7 } })`
  - *Available (7)*: OK, enabled with limit set to 7
  - *Available (5)*: error, limit value not available
  - *Unavailable*:   error, feature not available, limit key not available
  - *Unimplemented*: error, feature not available, limit key not available
- `a.requestDevice({ requiredFeatures: a.features, requiredLimits: { maxFoo:       undefined } })`
  - *Available (7)*: OK, enabled with limit set to default (5)
  - *Available (5)*: OK, enabled with limit set to default (5)
  - *Unavailable*:   OK, neither limit nor feature is requested
  - *Unimplemented*: OK, neither limit nor feature is requested
- `a.requestDevice({ requiredFeatures: a.features, requiredLimits: { maxFoo: a.limits.maxFoo } })`
  - *Available (7)*: OK, enabled with limit set to 7
  - *Available (5)*: OK, enabled with limit set to 5
  - *Unavailable*:   OK, neither limit nor feature is requested
  - *Unimplemented*: OK, neither limit nor feature is requested
- `a.requestDevice({ requiredFeatures: a.features, requiredLimits: { maxFoo:               5 } })`
  - *Available (7)*: OK, enabled with limit set to 5
  - *Available (5)*: OK, enabled with limit set to 5
  - *Unavailable*:   error, limit key not available
  - *Unimplemented*: error, limit key not available
- `a.requestDevice({ requiredFeatures: a.features, requiredLimits: { maxFoo:               7 } })`
  - *Available (7)*: OK, enabled with limit set to 7
  - *Available (5)*: error, limit value not available
  - *Unavailable*:   error, limit key not available
  - *Unimplemented*: error, limit key not available
