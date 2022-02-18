# Error Synchronicity Conventions/Guidelines

The behavior of every error case in WebGPU is defined by the spec on a
case-by-case basis. A given error has one of these behaviors:

* Synchronously throws a JS exception.
* Occurs asynchronously - one of:
  * Causes a WebGPU object to become internally null. Produces an error log entry.
  * Causes an operation to no-op. Produces an error log entry.
* If the operation returns a Promise, it rejects (and maybe produces an error log entry).

(If a "developer mode" is enabled, all validation errors are thrown
synchronously, as exceptions. Device loss may or may not be synchronous and
this behavior may be implementation-specific.
Out-of-memory errors should NOT be made synchronous if the application would
otherwise have an opportunity to recover from them.)

**The guidelines below are meant to help choose the individual cases defined by
the spec, but every case must be specced. This does not allow for
"implementation-defined" behavior.** Note that an implementation can easily
surface a synchronous error to the application "as-if" it's asynchronous, but
it cannot do the opposite, so we prefer to err on the side of asynchronicity in
the spec.

As a general rule, those error cases should follow the following guidelines,
but are allowed to deviate in individual cases. For WebGPU function call
`o.f(a, b, ...)`, let `A = {a: a, b: b, ...}` represent the object graph
passed into `o.f`.

* If WebIDL's binding rules would throw an exception: Error **must** be synchronous.
    E.g.:
    * If a parameter is passed in which doesn't match the type declared by the WebIDL.

* If the method `o.f` is part of a disabled feature: Error **must** be synchronous.
    * If the feature is *known but disabled*, `o.f` can be called, but
      throws an exception (in the implementation).
    * If the feature is *unknown*, `o.f` is `undefined`;
      calling `undefined` throws an exception.

* If the method `o.f` is available, but would return an instance of an
  interface defined in a disabled feature: Error **must** be synchronous.
    * (We probably won't have this case anyway.)

* If `o` **is** an interface (not an instance) that is defined in a disabled
  feature: Error **must** be synchronous. However, note that the behavior
  cannot match exactly:
    * If the feature is *known but disabled*, `o.f` can be called, but
      throws an exception (in the implementation).
    * If the feature is *unknown*, `o` is not defined, so accessing `o`
      throws an exception (and accessing `window.o` gives `undefined`).

* If any object in `A` contains any key that is not core or part of an enabled
  feature: Error **must** be synchronous.
    * This is explicitly made more strict than the usual WebIDL dictionary
      binding rules.

* If any object in `A` contains any key that is not known to the browser (is not
  present in its WebIDL code): No error.
    * This is how WebIDL works.
    * If possible browsers could choose to issue warnings for unrecognized keys.

* If any object in `A` sets any key that is known to the browser, but part of a
  non-enabled feature, is set to any value other than its default:
  Must be an error and the error **must not** be synchronous.

* If any object in `A` is missing a required key: Error **must** be synchronous
  (per WebIDL).
    * Dictionary members added to existing dictionaries by optional device
      features **must** be optional.

* Validation which affects content-timeline behavior:
  Error **should** be synchronous. E.g.:
    * Two arrays must match in length, but don't.
    * Offset/size parameters into a `ArrayBuffer`/`TypedArray` are
      out of bounds. (Avoids copying the whole ArrayBuffer across processes.)

* Validation which depends only on individual primitives (e.g. `Number`s) in
  `A`, `device.limits`, and `device.features`:
  Error **should not** be synchronous. E.g.:
    * A `Number` exceeds the associated entry in `limits`.
    * A bitflag has two incompatible bits.

* Validation which depends on state which *can be tracked* on the client-side:
  Error **may (but usually won't)** be synchronous. E.g.:
    * `queue.signalFence(fence, 3); queue.signalFence(fence, 2);`
    * Building an invalid command buffer (e.g. resource used in conflicting
      ways inside a pass): Not synchronous.

* Validation which depends on state which is *not synchronously known* on the
  client-side: Error **must not** be synchronous. E.g.:
    * A WebGPU interface object argument is invalid (due to validation or OOM).
    * The device is lost.
