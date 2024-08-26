// swift-tools-version:5.4
import PackageDescription

let package = Package(
    name: "TreeSitterWgsl",
    products: [
        .library(name: "TreeSitterWgsl", targets: ["TreeSitterWgsl"]),
    ],
    dependencies: [],
    targets: [
        .target(name: "TreeSitterWgsl",
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
                    "src/parser.cpp",
                    "src/scanner.cpp",
                ],
                resources: [
                    .copy("queries")
                ],
                publicHeadersPath: "bindings/swift",
                cxxSettings: [.headerSearchPath("src")]),
    ],
    cxxLanguageStandard: .cxx17
)
