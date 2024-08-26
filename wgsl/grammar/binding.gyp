{
  "targets": [
    {
      "target_name": "tree_sitter_wgsl_binding",
      "dependencies": [
        "<!(node -p \"require('node-addon-api').targets\"):node_addon_api_except",
      ],
      "include_dirs": [
        "src",
      ],
      "sources": [
        "bindings/node/binding.cc",
        "src/parser.cpp",
        "src/scanner.cpp",
      ],
      "conditions": [
        ["OS!='win'", {
          "cflags_cc": [
            "-std=c++17",
          ],
        }, { # OS == "win"
          "cflags_cc": [
            "/std:c++17",
            "/utf-8",
          ],
        }],
      ],
    }
  ]
}
