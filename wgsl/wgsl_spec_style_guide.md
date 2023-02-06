# WSGL spec writing style guide

## Style

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
*   Avoiding passive voice is one way to achive the needed clarity.

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

The WGSL grammar's syntactic rules are presented as a set of cross-referenced Bikeshed
definitions. There is one Bikeshed definition for each grammar token or non-terminal.
These definitions are contained in `` div `` elements in the `` syntax `` class.

Authoring syntactic rules:
* Each syntactic rule should start with a line which only contains `` <div class='syntax' noexport='true'> ``
and end with a line which only contains `` </div> ``. There must be only one
syntactic rule between these lines.
* Each syntactic rule must define itself for Bikeshed. Each syntactic rule definition must start with two spaces
and then place the rule name between `` <dfn for=syntax> `` and `` </dfn> : `` on the same line.
* Each syntactic rule item must start with four spaces and then list members after `` | `` followed by a space.
    * Syntactic rule items can be split to multiple lines. For this, start the next line with six spaces.
* Each syntactic rule item must be surrounded by only a space before and after,
trailing space at the end of the line being redundant.
* Members of syntactic rules items can be references to existing rules. These must be placed between
`` [=syntax/ `` and `` =] ``.
* Members of syntactic rules can contain groups which should contain the group members between `` ( `` and `` ) ``.
* Members of syntactic rule items which denote a string should start with `` `' ``
and end with `` '` `` and not contain any space character or line break between these two.
* Members of syntactic rule items which denote a regular expression should start with `` `/ ``
and end with `` /` `` and not contain any space character or line break between these two.
* If a member is optional, then it must be followed by a `` ? `` member token.
* If a member can repeat and must appear at least once, then it must be followed by a `` + `` member token.
* If a member can repeat and does not have to appear, then it must be followed by a `` * `` member token.

WGSL specification normalizes its normative and informative sources to
promote interoperability between developers using different input mechanisms.
A developer intending to contribute can automatically normalize sources by
passing `--fix` to `check-nfkc.py` in the tools directory.

## Tagging conventions

Several tools process the specification source, extracting things for further processing.
Those tools rely on attributes on certain elements, as described here.

### Algorithms

In [Bikeshed][] source, an [algorithm](https://tabatkins.github.io/bikeshed/#algorithms)
attribute on an element does two things:

1. It specifies a unique human-readable name for the thing being defined by the element.
1. It scopes variables to that element. In a browser, clicking on one use of a variable
    will highlight all the uses of that variable in the same scope.

For example, the definition of a matrix type has two parameters: _C_ and _R_.
The uses of `|C|` and `|R|` are scoped to the `tr` element having the `algorithm` attribute:

    <tr algorithm="matrix type">
      <td>mat|C|x|R|&lt;f32&gt;
      <td>Matrix of |C| columns and |R| rows, where |C| and |R| are both in {2, 3, 4}.
          Equivalently, it can be viewed as |C| column vectors of type vec|R|&lt;f32&gt;.

The following kinds of document elements should have `algorithm` attribute:

* Types:  Tag the `tr` element in the table describing the type.
* Each row (`tr` element) in a [type rule table](https://w3.org/TR/WGSL#typing-tables-section):
    * This applies to the tables describing expressions and built-in functions.
* Parameterized definitions, equations, or rules that have variables:
    * These use `p`, `blockquote`, or `div` elements.

### Code samples

Code samples should have a `class` attribute starting with `example`.

For WGSL code samples, specify a `class` tag whose value is three space-separated words:
* `example` indicating this is a code example
* `wgsl` indicating the code is in WGSL
* a word indicating what kind of code snippet it is, or where it should appear, one of:
   * `expect-error`: The code snippet is invalid
   * `global-scope`: The code snippet is assumed to appear at module-scope, i.e. outside all other declarations.
   * `type-scope`: The code snippet shows the WGSL spelling of a type, independent of other context.
   * `function-scope`: The code snippet is assumed to appear inside a function body, but the function declaration
         and surrounding braces are not shown.

For example:

    <div class='example wgsl global-scope' heading='Trivial fragment shader'>
      <xmp highlight='rust'>
        @stage(fragment)
        fn main() -> @location(0) vec4<f32> {
          return vec4<f32>(0.4,0.4,0.8,1.0);
        }
      </xmp>
    <div>


Code samples in languages other than WGSL should name the language, for example:

    <div class='example spirv barrier mapping' heading="Mapping workgroupBarrier to SPIR-V">


## In-progress extensions are developed outside the main spec text

Once a language extension is fully developed, it should be described in the WGSL specification.

Before then, an extension is considered to be "in progress", and should not be discussed in the main WGSL specification.
Extensions which require a lot of iteration can be freely developed in a branch or some other document.

[Bikeshed]: https://tabatkins.github.io/bikeshed "Bikeshed"
