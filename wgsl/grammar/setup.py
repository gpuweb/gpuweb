from os.path import isdir, join
from platform import system

from setuptools import Extension, find_packages, setup
from setuptools.command.build import build
from wheel.bdist_wheel import bdist_wheel

class Build(build):
    def run(self):
        dest = join(self.build_lib, "tree_sitter_wgsl", "src")
        self.copy_tree("src", dest)
        if isdir("queries"):
            dest = join(self.build_lib, "tree_sitter_wgsl", "queries")
            self.copy_tree("queries", dest)
        super().run()


class BdistWheel(bdist_wheel):
    def get_tag(self):
        python, abi, platform = super().get_tag()
        if python.startswith("cp"):
            python, abi = "cp38", "abi3"
        return python, abi, platform


setup(
    packages=find_packages("bindings/python"),
    package_dir={"": "bindings/python"},
    package_data={
        "tree_sitter_wgsl": ["*.pyi", "py.typed"],
        "tree_sitter_wgsl.queries": ["*.scm"],
    },
    ext_package="tree_sitter_wgsl",
    ext_modules=[
        Extension(
            name="_binding",
            sources=[
                "bindings/python/tree_sitter_wgsl/binding.cpp",
                "src/parser.cpp",
                "src/scanner.cpp",
            ],
            extra_compile_args=[
                "-std=c++17",
            ] if system() != "Windows" else [
                "/std:c++17",
                "/utf-8",
            ],
            define_macros=[
                ("Py_LIMITED_API", "0x03080000"),
                ("PY_SSIZE_T_CLEAN", None)
            ],
            include_dirs=["src", "src/tree_sitter"],
            py_limited_api=True,
        )
    ],
    cmdclass={
        "build": Build,
        "bdist_wheel": BdistWheel
    },
    zip_safe=False
)
