# WGSL Namespaces

* Status: [Draft](README.md#status-draft)
* Created: 2026-09-01
* Issue: [#777](https://github.com/gpuweb/gpuweb/issues/777)

## Motivation

There is currently no namespacing support in WGSL. This is an issue if a user
shadows a builtin (say `min`) they can no-longer use the WGSL `min` method. As
well, as folks create JS files which get stitched together there is no easy way,
besides name prefixing, to make sure that a name from one file does not collide
with another. Providing simple namespacing support would fix both of these issues.

## WGSL

### Language Extension

| Name    | Description |
| ------- | ----------- |
| `namespaces`   | Adds the ability to declare and access `namespace`'s |

### Example Usage

```wgsl
namespace helpers {
namespace nested::comparison {
  fn min(a: u32, b: u32) {
    return b;
  }
}

const kHelperValue = 2u;
override SpecialValue = 3u;

fn min(a: u32, b: u32, c: u32) {
  return nested::comparison::min(a, c);
}

}

fn b() {
  let a = helpers::min(1u, 2u, 3u);
  let b = wgsl::min(helpers::kHelperValue, 3u);
  let c = min(2u, 3u);  // Gets the WGSL version since it's available globally.
}
```

## Description

A namespace is declared with the `namespace` keyword. It accepts a single
argument followed by a block. The name argument and block are both required.
The `::` can be used to create nested namespaces. There is no anonymous
namespace. Declarations inside a namespace are order-independent.

Methods in the immediate namespace block can be accessed without prefixing,
otherwise the full namespace prefix must be used (even if accessing a parent
namespace). This rule does mean that moving existing code into a namespace may
require updates to names (e.g. If I have namespace B accessing things X,Y at
global scope, then wrap both B and X and Y with outer namepace A, then I have to
modify code inside of B to do that). Having this namespace lookup rule greatly
reduces the amount of work required to do name lookup. You will look in the
current scope, otherwise you have the fully namespaced scope to look through.
You are not required to search sibling scopes, or nested sibling scopes for names.

**Q:** Walking up scopes for namespacing is more similar to existing WGSL things,
but, at least in c++ there are a lot of edge cases around this lookup.

A namespace can be re-opened by declaring the same namespace name again later,
the new methods, constants, etc will be added into the existing namespace.

**Q:** Do we want to allow reopening? It seems handy, but first time we can
"re-open" something in WGSL

When an `override` is declared in a namespace, then the names set on the API
side is the fully qualified name, so `helpers::SpecialValue` is required
to be provided.

An entry point declared in a namespace must be referred to by the fully
qualified name from the API.

A `using` statement is provided in order to pull the names from a namespace into
the current scope. This effectively makes the names available with the provided
namespace prefix removed. The usual scoping rules apply in that the names pulled
in from the namespace must not collide with any other names already in scope.

```wgsl
using namespace test;  // Order independent of the namespace declaration

namespace test {
fn helper() {}
}

fn test_helper() {
  helper();
}
```

The `wgsl::` namespace is reserved. It cannot be re-opened (TODO if reopen is
supported) by users. The contents of the `wgsl::` namespace may be accessed
unprefixed in all cases, the namespace is optional. Essentially, there is an
implicit `using namespace wgsl` at the start of every WGSL program. (Note, the
WGSL pseudo-using is in a scope above module scope. This allows the WGSL names
to be shadowed in the user programs. Essentially, how WGSL works now, just with
the `using` concept.)

## Validation

* Namespace must have a name
* Name must be a sequence of 1 or more valid WGSL identifiers, separated by
  `::`. There may be blankspace between the identifiers and the `::`.
* Namespace must have a `{}`
* Namespace must only appear at module scope or nested inside a namespace

## Grammar

```ebnf
global_decl:
  ...
  | namespace_decl

namespace_ident:
  ident
  | ident `::` namespace_ident

namespace_decl:
  'namespace' namespace_ident namespace_body_decl

namespace_body_decl:
  `{` global_decl `}`  // May not be global_decl depending on var and override support
```

# Alternatives

* Do nothing, do not provide namespaces
