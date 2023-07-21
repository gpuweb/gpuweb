# Building the WebGPU/WGSL specs

**See [README.md](README.md) for procedural information about contributing.**

**See [wgsl/README.md](wgsl/README.md) for more details about building the WGSL spec.**

## Setting up a working environment

### Using GitHub Codespaces

A GitHub Codespace is a very convenient way to make changes without setting up toolchains locally.
It requires an internet connection and may be a little slower to build than your local machine.

> The Free and Pro plans for personal accounts include free use of GitHub Codespaces up to a fixed amount of usage every month.

For more info on GitHub Codespaces billing, see [this help page](https://docs.github.com/en/billing/managing-billing-for-github-codespaces/about-billing-for-github-codespaces).

1. Fork the repository at <https://github.com/gpuweb/gpuweb/fork>
1. On your fork:
    1. Click the big green "Code" button
    1. Switch to the "Codespaces" tab
    1. Click the "+" to create a new Codespace

    This will open the Codespace in a tab. To get back to it:

    1. Click the big green "Code" button (on your fork or the upstream repository gpuweb/gpuweb)
    1. Switch to the "Codespaces" tab
    1. Click on the name of your Codespace
1. Using the built-in terminal:
    1. Create a branch: `git checkout -b my-new-change`
    1. See the "Building"/"Previewing" instructions below.

    1. When you start a web server inside the Codespace, you'll get a notification on
        the editor page. Click on it to get to the web-visible URL for your server.

### Using the Dev Container locally

Please see <https://docs.github.com/en/codespaces/developing-in-codespaces/creating-a-codespace-for-a-repository>.

### Using your local system without the Dev Container

On a local system, you'll need to install dependencies.
To install all tools, run:

```bash
./tools/install-dependencies.sh bikeshed diagrams wgsl
```

(Alternatively, you can invoke `pip3`/`npx` directly, using the commands in
[that script](../tools/install-dependencies.sh).) More details:

The specifications are written using [Bikeshed](https://tabatkins.github.io/bikeshed).
Installing Bikeshed is optional; if Bikeshed is not installed locally,
the Bikeshed API will be used to generate the specification
(but this is generally slower).

Diagrams generated using [Mermaid](https://mermaid-js.github.io/mermaid/).
This isn't required unless you're modifying or creating diagrams.

The WGSL spec uses some additional tools for language parsing;
see [wgsl/README.md](wgsl/README.md) if you want to know more.

## Building this spec

To build all documents:

```bash
make -j
```

To build just the WebGPU specification (`spec/index.html`):

```bash
make -C spec index.html
```

To build just the WGSL specification (`wgsl/index.html`):

```bash
make -C wgsl index.html
```

Alternatively, `cd` into your target document's subdirectory, and call `make` or `make -j`.

**Both `spec` and `wgsl` also have other targets in their `Makefile`s, which are documented inline.**

The other documents in this repository (`correspondence` and `explainer`) can be built similarly.

## Previewing the spec

Launch a local web server to preview your spec changes, for example:

```bash
python3 -m http.server
```

(Add `-b localhost` if developing locally so the port won't be exposed to your network.)

or:

```bash
npx http-server
```

(Add `-a localhost` if developing locally so the port won't be exposed to your network.)
