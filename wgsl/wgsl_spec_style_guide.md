# WSGL spec writing style guide

Goal:  Avoid possibly being misunderstood.
*   Tradeoff: The text might read as stilted.  **Precision is better than flair.**

Prefer short sentences.

Be clear about which agent is doing what:
*   The _shader author_ is the person writing the WGSL code for use in their application
*   The _implementation_ is the thing that runs the application, processing the WGSL code.
    *   Implicitly, the implementation is a hardware-software combination, and the
        normative part of the specification does not care about the boundary between them.
        However, non-normative explanatory text can call out common cases, to aid the
        reader's understanding.
    *   Avoid overly specific terms like “hardware” or “instructions” in the normative
        part of the text.
*   Avoid using “we”, as that is often ambiguous.
    *   Exception: It’s ok to write “We say” to introduce alternative terminology.
*   Avoiding passive voice is one way to achive the needed clairty.

Use “must” when there is an absolute requirement to satisfy a condition, either on the part of
the shader author or the implementation.
*   See  [RFC 2119 - Key words for use in RFCs to Indicate Requirement Levels](https://tools.ietf.org/html/rfc2119)
*   Using consistent phrasing makes it easy to find validation rules.

Note:  When the shader author violates a “must” rule,
the result is either a static error (discoverable by inspecting the source alone),
or a dynamic error (a condition which only occurs at runtime, and might not even be detectable).
It is not yet decided what should occur for a dynamic error.

Avoid complexity by breaking up compounds:
*   Never combine "and" and "or" cases in the same sentence.
*   Convert "and"s into a bulleted list
*   Convert "or"s into a bulleted list

One way to break up a compound is to list options:

> An array element type must be one of:
> *   a [scalar](https://gpuweb.github.io/gpuweb/wgsl.html#scalar) type
> *   a vector type
> *   a matrix type
> *   an array type
> *   a [structure](https://gpuweb.github.io/gpuweb/wgsl.html#structure) type

Another way is to use “legal-style” logical connectives between items, for example:

> Produce a validation error if:
> *   Foo is not frobulated, and
> *   Foo is a zozor, and
> *   The parent of Foo was created in a mittens context

When in doubt, start with a definition.
Later text can refer to the concept unambiguously.

Replace "all" by "each".
*   Avoids a many-to-one or many-to-many ambiguity.

Say it twice: with definitions, then examples.

Writing a section (guidance):
1. Optional: Motivation; short.
2. Definition.  An authoritative name for a concept.
    1. It’s a crisp statement of what a THING is, and what is not a THING. (Crisp = precise; also brief, if possible)
        1. Rely on common English terms.
        2. Rely on common practice in the domain. BUT, follow up with a rule that pins it down _for this specification_.
    2. Example, "numeric scalar".
3. State rules for the THING.  This ties to context in other sections.
4. Grammar, if it can be localized.  (Maybe somewhere else? Don’t want to interrupt the reader flow.)
5. Optional: Describe typical usage scenario.
6. Optional, encouraged: Examples (typical)
7. Optional: Exceptional usage.
8. Optional: Connecting to other sections/concepts.

When there is an interaction between WebGPU and WGSL specs,
write the rules in the WebGPU spec, not the other way around.
*   Limit interactions as much as possible.
*   The rules (in WebGPU) should reference defined terms in WGSL.

Use the [serial comma](https://en.wikipedia.org/wiki/Serial_comma), also known as the Oxford comma.

In Markdown, no two sentences (or parts of sentences) should be on the same text line.
This makes it easier to edit and review changes.
