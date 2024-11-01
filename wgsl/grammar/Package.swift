// swift-tools-version:5.4
import PackageDescription

let package = Package(
    name: "TreeSitterWgsl",
    products: [
        .library(name: "TreeSitterWgsl", targets: ["TreeSitterWgsl"]),
    ],
    dependencies: [
        .package(url: "https://github.com/ChimeHQ/SwiftTreeSitter", from: "0.8.0"),
    ],
    targets: [
        .target(
            name: "TreeSitterWgsl",
            dependencies: [],
            path: ".",
            exclude: [
                "Cargo.toml",
                "Makefile",
                "binding.gyp",
                "bindings/c",
                "bindings/go",
                "bindings/node",
                "bindings/python",
                "bindings/rust",
                "prebuilds",
                "grammar.js",
                "package.json",
                "package-lock.json",
                "pyproject.toml",
                "setup.py",
                "test",
                "examples",
                ".editorconfig",
                ".github",
                ".gitignore",
                ".gitattributes",
                ".gitmodules",
            ],
            sources: [
                "src/parser.c",
                // NOTE: if your language has an external scanner, add it here.
                "src/scanner.c",
            ],
            resources: [
                .copy("queries")
            ],
            publicHeadersPath: "bindings/swift",
            cSettings: [.headerSearchPath("src")]
        ),
        .testTarget(
            name: "TreeSitterWgslTests",
            dependencies: [
                "SwiftTreeSitter",
                "TreeSitterWgsl",
            ],
            path: "bindings/swift/TreeSitterWgslTests"
        )
    ],
    cLanguageStandard: .c11
)
