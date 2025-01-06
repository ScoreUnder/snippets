#!/usr/bin/env python3
# mypy: disallow_redefinition = False
# pylint: disable=no-else-return
"""
Quick and dirty script to generate a graph of installed pacman packages and their dependencies,
with a focus on the size of the packages.
"""

import argparse
from collections import defaultdict
from functools import partial
import os
import subprocess
import sys
import threading
from tqdm import tqdm

TYPING = False

if TYPING:
    from typing import (
        Callable,
        Dict,
        FrozenSet,
        IO,
        Iterable,
        Iterator,
        List,
        Optional,
        Set,
        Tuple,
    )
    from typing_extensions import Literal

_units = {
    "B": 1,
    "KiB": 1024,
    "MiB": 1024**2,
    "GiB": 1024**3,
    "TiB": 1024**4,
}


class DebuggedStream:
    """
    Context manager that records the last few lines of a stream, and prints them if an exception
    occurs.
    """

    stream: "Iterable[str]"
    debug_last_few_lines: "List[str]"
    num_lines: int

    def __init__(self, stream: "Iterable[str]", num_lines: int = 10):
        self.stream = stream
        self.debug_last_few_lines = []
        self.num_lines = num_lines

    def __enter__(self) -> "DebuggedStream":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> "Literal[False]":
        if exc_type is not None:
            if self.debug_last_few_lines:
                print("Last few lines of stream:", file=sys.stderr)
                for line in self.debug_last_few_lines:
                    print(line.rstrip(), file=sys.stderr)

        return False

    def _recording_generator(self) -> "Iterator[str]":
        for line in self.stream:
            self.debug_last_few_lines.append(line)
            if len(self.debug_last_few_lines) > 10:
                self.debug_last_few_lines.pop(0)
            yield line

    def __iter__(self) -> "Iterator[str]":
        return self._recording_generator()


def parse_size(size: str) -> int:
    """
    Parse a size string from the pacman database, and return the size in bytes.
    """
    num_str, unit = size.split()
    num = float(num_str) * _units[unit]
    return int(num)


def format_size(size: int) -> str:
    """
    Format a size in bytes as a human-readable string.
    """
    if size < 1024:
        return f"{size} B"
    elif size < 1024**2:
        return f"{size / 1024:.2f} KiB"
    elif size < 1024**3:
        return f"{size / 1024**2:.2f} MiB"
    elif size < 1024**4:
        return f"{size / 1024**3:.2f} GiB"
    else:
        return f"{size / 1024**4:.2f} TiB"


class PacmanPackage:
    """
    Represents a single package in the pacman database.
    """

    __slots__ = "name", "dependencies", "optional_dependencies", "size"

    name: str
    dependencies: "Set[str]"
    optional_dependencies: "Set[str]"
    size: "Optional[int]"

    def __init__(self, name: str):
        self.name = name
        self.dependencies = set()
        self.optional_dependencies = set()
        self.size = None

    def __repr__(self) -> str:
        return (
            "PacmanPackage("
            f"{self.name!r}, {self.dependencies!r}, {self.optional_dependencies!r}, {self.size!r}"
            ")"
        )

    @staticmethod
    def strip_version_requirements(name: str) -> str:
        """
        Strip version requirements from a package name.
        """
        if ">" in name:
            return name[: name.index(">")]
        elif "<" in name:
            return name[: name.index("<")]
        elif "=" in name:
            return name[: name.index("=")]
        return name


class PacmanInstalledSet:
    """
    Represents the set of installed packages in the pacman database, with their dependencies.
    """

    __slots__ = (
        "packages",
        "unknowns",
        "aliases",
        "revdep_cache",
        "retained_set_cache",
    )

    packages: "Dict[str, PacmanPackage]"
    unknowns: "Set[str]"
    aliases: "Dict[str, str]"
    revdep_cache: "Optional[Dict[str, Set[str]]]"
    retained_set_cache: "Dict[str, FrozenSet[str]]"

    def __init__(self):
        self.packages = {}
        self.unknowns = set()
        self.aliases = {}
        self.revdep_cache = None
        self.retained_set_cache = {}

    def add_package(self, name: str):
        """
        Add a package to the set of installed packages.
        """
        if name is None:
            raise ValueError("Package name is None")
        if name in self.packages:
            raise ValueError(f"Package {name} already added")
        self.packages[name] = PacmanPackage(name)
        self.unknowns.discard(name)

    def add_dependency(self, package: str, dependency: str):
        """
        Add a dependency from one package to another.
        """
        if package is None:
            raise ValueError("Package name is None")
        if dependency is None:
            raise ValueError("Dependency name is None")
        if package not in self.packages:
            raise ValueError(f"Package {package} not added yet")
        if dependency not in self.packages and dependency not in self.aliases:
            self.unknowns.add(dependency)
        self.packages[package].dependencies.add(dependency)

    def add_optional_dependency(self, package: str, dependency: str):
        """
        Add an optional dependency from one package to another.
        Does not record the reason for the dependency.
        """
        if package is None:
            raise ValueError("Package name is None")
        if dependency is None:
            raise ValueError("Dependency name is None")
        if package not in self.packages:
            raise ValueError(f"Package {package} not added yet")
        self.packages[package].optional_dependencies.add(dependency)

    def add_alias(self, alias: str, target: str):
        """
        Add an alias for a package.
        """
        if alias is None:
            raise ValueError("Alias name is None")
        if target is None:
            raise ValueError("Target name is None")
        self.aliases[alias] = target
        self.unknowns.discard(alias)

    def resolve_alias(self, alias: str) -> str:
        """
        Resolve an alias to the target package name.
        If an alias shares a name with a package, it is returned unchanged
        (i.e. the package takes precedence).
        """
        if alias in self.packages or alias in self.unknowns:
            return alias
        return self.aliases.get(alias, alias)

    def finalise_dependency_sets(self):
        """
        Resolve all aliases in package dependencies, and remove non-installed optional dependencies.
        """
        self.revdep_cache = revdep_cache = defaultdict(set)

        for package in self.packages.values():
            package.dependencies = {
                self.resolve_alias(name) for name in package.dependencies
            }
            package.optional_dependencies = {
                name
                for name in (
                    self.resolve_alias(name) for name in package.optional_dependencies
                )
                if name in self.packages
            }

            package_name = package.name
            for dependency in package.dependencies:
                revdep_cache[dependency].add(package_name)

    def __getitem__(self, key: str) -> PacmanPackage:
        if key in self.aliases and key not in self.packages:
            key = self.aliases[key]
        return self.packages[key]

    def compute_retained_set_internal(
        self, package: str, parents: "FrozenSet[str]"
    ) -> "Tuple[FrozenSet[str], FrozenSet[str]]":
        """
        Compute the set of packages retained by a package, including its dependencies.
        """
        if package in self.retained_set_cache:
            return self.retained_set_cache[package], frozenset()
        old_name = package
        package = self.resolve_alias(package)
        if package in self.retained_set_cache:
            self.retained_set_cache[old_name] = self.retained_set_cache[package]
            return self.retained_set_cache[package], frozenset()

        retained_set = {package}
        parents = parents | {package}
        dependencies = self.packages[package].dependencies
        cycle_set: Set[str] = dependencies & parents
        for dependency in dependencies - cycle_set:
            next_retained_set, next_cycle_set = self.compute_retained_set_internal(
                dependency, parents
            )
            retained_set |= next_retained_set
            cycle_set |= next_cycle_set

        cycle_set.discard(package)

        retained_set: FrozenSet[str] = frozenset(retained_set)
        if not cycle_set:
            # If we're not in a dependency cycle, we definitely have the full view
            # So cache the result
            self.retained_set_cache[package] = retained_set

        return retained_set, frozenset(cycle_set)

    def compute_retained_set(self, packages: "Iterable[str]") -> "Set[str]":
        """
        Compute the set of packages retained by a set of packages, including their dependencies.
        This is a more efficient version that caches the results for each package.
        """
        return set().union(
            *(
                self.compute_retained_set_internal(package, frozenset())[0]
                for package in ([packages] if isinstance(packages, str) else packages)
            )
        )

    def compute_retained_size(self, packages: "Iterable[str]") -> int:
        """
        Compute the retained size of a set of packages, including their dependencies.
        """
        return sum(
            self[package].size or 0 for package in self.compute_retained_set(packages)
        )

    def compute_adjusted_size(self, packages: "Iterable[str]") -> int:
        """
        Compute the adjusted size of a set of packages, including their dependencies.
        This is similar to the retained size, but weights dependencies according to
        roughly the inverse of how many reverse dependencies they have.
        """
        if self.revdep_cache is None:
            raise ValueError("Dependency sets not finalised")

        if isinstance(packages, str):
            packages = {packages}
        else:
            packages = set(packages)

        packages = set(self.resolve_alias(name) for name in packages)
        adjusted_size = float(sum(self[package].size or 0 for package in packages))

        retained_set = self.compute_retained_set(frozenset(packages))

        for package in retained_set - packages:
            revdeps = self.revdep_cache[package]
            weight = sum(
                1 if revdep in retained_set else 0 for revdep in revdeps
            ) / len(revdeps)
            size = self[package].size or 0
            adjusted_size += size * weight

        return int(adjusted_size)

    def compute_uniquely_retained_size(self, packages: "Iterable[str]") -> int:
        """
        Compute the size of packages that are only retained by the given set of packages.
        """
        if isinstance(packages, str):
            packages = {packages}
        else:
            packages = set(packages)

        packages = set(self.resolve_alias(name) for name in packages)

        revdep_cache = self.revdep_cache
        if revdep_cache is None:
            raise ValueError("Dependency sets not finalised")

        uniquely_retained_set = set(packages)
        queue: "List[str]" = []

        iters = 0
        old_length = 0
        while len(uniquely_retained_set) > old_length:
            iters += 1
            old_length = len(uniquely_retained_set)
            queue.extend(uniquely_retained_set)
            while queue:
                package = queue.pop()
                unique_deps = set(
                    dep
                    for dep in self.packages[package].dependencies
                    if uniquely_retained_set.issuperset(revdep_cache[dep])
                )
                queue.extend(unique_deps - uniquely_retained_set)
                uniquely_retained_set |= unique_deps

        if iters > 1:
            print(
                f"Uniquely retained set took {iters} iterations to stabilise for {packages}."
                f"Result: {uniquely_retained_set}",
                file=sys.stderr,
            )

        return sum(
            self.packages[package].size or 0 for package in uniquely_retained_set
        )

    @staticmethod
    def from_pacman_qi_stream(stream: "Iterable[str]") -> "PacmanInstalledSet":
        """
        Parse the output of `pacman -Qi` from a stream, and return a PacmanInstalledSet object.
        """
        installed_set = PacmanInstalledSet()
        current_package: Optional[str] = None
        key = ""
        with DebuggedStream(stream) as stream_debug:
            t = tqdm(
                total=float("inf"),
                unit="packages",
                desc="Parsing pacman -Qi",
                leave=False,
            )
            for line in stream_debug:
                # "Optional Deps   : "
                # #012345678901234567
                # #0         1
                # line[16] == ':'

                if len(line) < 17:
                    if line.strip():
                        raise ValueError(f"Short line: {line}")

                    key = ""
                    current_package = None
                    continue

                value = line[17:].strip()

                if line[16] == ":":
                    key = line[:16].strip()
                    if value == "None":
                        # e.g. "Provides        : None"
                        continue
                elif key != "Optional Deps":
                    raise ValueError(
                        f"Continuation of previous line not in optdeps: {value!r} in key {key!r}"
                    )

                if key == "Name":
                    current_package = value.strip()
                    installed_set.add_package(current_package)
                    t.update()
                elif key == "Depends On":
                    if current_package is None:
                        raise ValueError("No package name found before dependencies")
                    for dependency in value.split():
                        dependency = PacmanPackage.strip_version_requirements(
                            dependency
                        )
                        installed_set.add_dependency(current_package, dependency)
                elif key == "Optional Deps":
                    if current_package is None:
                        raise ValueError(
                            "No package name found before optional dependencies"
                        )
                    if ":" in value:
                        value = value[: value.index(":")]
                        value = value.strip()
                        value = PacmanPackage.strip_version_requirements(value)
                    installed_set.add_optional_dependency(current_package, value)
                elif key == "Installed Size":
                    if current_package is None:
                        raise ValueError("No package name found before size")
                    installed_set.packages[current_package].size = parse_size(
                        value.strip()
                    )
                elif key == "Provides":
                    if current_package is None:
                        raise ValueError("No package name found before provides")
                    for provided in value.split():
                        provided = PacmanPackage.strip_version_requirements(provided)
                        installed_set.add_alias(provided, current_package)
            t.close()

        installed_set.finalise_dependency_sets()
        return installed_set

    def __repr__(self) -> str:
        return (
            "PacmanInstalledSet("
            f"{self.packages!r}, {self.unknowns!r}, {self.revdep_cache!r}, {self.aliases!r}"
            ")"
        )

    @staticmethod
    def retrieve_pacman_packages():
        """
        Retrieve the list of installed packages from pacman, and return
        a PacmanInstalledSet object.
        """

        # Use cache first
        try:
            with open("pacman_qi.txt", "r", encoding="utf-8") as file:
                return PacmanInstalledSet.from_pacman_qi_stream(file)
        except FileNotFoundError:
            pass

        env = dict(os.environ, LC_ALL="C", LANG="C", TERM="dumb")
        for bad_key in "TTY", "ROWS", "COLUMNS":
            env.pop(bad_key, None)

        with subprocess.Popen(
            ["pacman", "-Qi"],
            stdout=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        ) as proc:

            def drain_stderr():
                for line in proc.stderr:
                    print("Pacman stderr:", line, end="", file=sys.stderr)

            stderr_thread = threading.Thread(target=drain_stderr, daemon=True)
            stderr_thread.start()

            return PacmanInstalledSet.from_pacman_qi_stream(proc.stdout)


class OkLabTransform:
    @staticmethod
    def rgb_linearise(value: float) -> float:
        if value >= 0.0031308:
            return (1.055) * value ** (1.0 / 2.4) - 0.055
        else:
            return 12.92 * value

    @staticmethod
    def rgb_delinearise(value: float) -> float:
        if value >= 0.04045:
            return ((value + 0.055) / (1 + 0.055)) ** 2.4
        else:
            return value / 12.92

    @staticmethod
    def from_rgb(r: float, g: float, b: float) -> "Tuple[float, float, float]":
        r = OkLabTransform.rgb_delinearise(r)
        g = OkLabTransform.rgb_delinearise(g)
        b = OkLabTransform.rgb_delinearise(b)
        l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
        m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
        s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b

        l_ = l ** (1 / 3)
        m_ = m ** (1 / 3)
        s_ = s ** (1 / 3)

        return (
            0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
            1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
            0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
        )

    @staticmethod
    def to_rgb(l: float, a: float, b: float) -> "Tuple[float, float, float]":
        l_ = l + 0.3963377774 * a + 0.2158037573 * b
        m_ = l - 0.1055613458 * a - 0.0638541728 * b
        s_ = l - 0.0894841775 * a - 1.2914855480 * b

        l = l_**3
        m = m_**3
        s = s_**3

        r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
        g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
        b = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s

        return (
            OkLabTransform.rgb_linearise(r),
            OkLabTransform.rgb_linearise(g),
            OkLabTransform.rgb_linearise(b),
        )


def lerp_vec3(
    a: "Tuple[float, float, float]", b: "Tuple[float, float, float]", t: float
) -> "Tuple[float, float, float]":
    return (
        a[0] * (1 - t) + b[0] * t,
        a[1] * (1 - t) + b[1] * t,
        a[2] * (1 - t) + b[2] * t,
    )


def clamp_vec3(value: "Tuple[float, float, float]") -> "Tuple[float, float, float]":
    return (
        max(0, min(1, value[0])),
        max(0, min(1, value[1])),
        max(0, min(1, value[2])),
    )


def heatmap_colouring(
    min_value: float, max_value: float, palette: "List[Tuple[float, float, float]]"
):
    if len(palette) < 2:
        raise ValueError("Palette must have at least two colours")

    colourspace = OkLabTransform
    palette = [colourspace.from_rgb(*rgb) for rgb in palette]

    transform = lambda v: v**0.1

    min_value = transform(min_value)
    value_range = transform(max_value - min_value)

    def colour(value: float) -> "Tuple[float, float, float]":
        if value <= min_value:
            return palette[0]
        if value >= max_value:
            return palette[-1]

        value = transform(value - min_value)
        t = value / value_range
        if t <= 0:
            return palette[0]
        if t >= 1:
            return palette[-1]

        t *= len(palette) - 1
        i = int(t)
        t -= i
        return clamp_vec3(colourspace.to_rgb(*lerp_vec3(palette[i], palette[i + 1], t)))

    return colour


class SizeFormatter:
    name: str

    def get_size(
        self, installed_set: PacmanInstalledSet, package: PacmanPackage
    ) -> int:
        raise NotImplementedError()

    def format_size(self, size: int) -> str:
        return format_size(size)


class OwnSizeFormatter(SizeFormatter):
    name = "own"

    def get_size(
        self, installed_set: PacmanInstalledSet, package: PacmanPackage
    ) -> int:
        return package.size or 0


class RetainedSizeFormatter(SizeFormatter):
    name = "retained"

    def get_size(
        self, installed_set: PacmanInstalledSet, package: PacmanPackage
    ) -> int:
        return installed_set.compute_retained_size(package.name)


class AdjustedSizeFormatter(SizeFormatter):
    name = "adjusted"

    def get_size(
        self, installed_set: PacmanInstalledSet, package: PacmanPackage
    ) -> int:
        return installed_set.compute_adjusted_size(package.name)


class UniquelyRetainedSizeFormatter(SizeFormatter):
    name = "uniquely retained"

    def get_size(
        self, installed_set: PacmanInstalledSet, package: PacmanPackage
    ) -> int:
        return installed_set.compute_uniquely_retained_size(package.name)


class RetainedPackagesFormatter(SizeFormatter):
    name = "retained packages"

    def get_size(
        self, installed_set: PacmanInstalledSet, package: PacmanPackage
    ) -> int:
        return len(installed_set.compute_retained_set(package.name))

    def format_size(self, size: int) -> str:
        return str(size)


def make_graph(
    installed_set: PacmanInstalledSet,
    size_formatter: SizeFormatter,
    output_file: "IO[str]",
    filter_func: "Optional[Callable[[PacmanPackage], bool]]" = None,
    include_optional: bool = False,
):
    size_calc = partial(size_formatter.get_size, installed_set)
    format_size = size_formatter.format_size
    if filter_func is None:
        filter_func = lambda _: True

    package_sizes = {
        package.name: size_calc(package)
        for package in tqdm(
            installed_set.packages.values(),
            desc="Computing package sizes",
            unit="packages",
        )
    }
    max_size = max(package_sizes.values())

    if size_formatter.name == "own":
        # Switch to retained size for display
        size_formatter = RetainedSizeFormatter()
        display_package_sizes = {
            package.name: installed_set.compute_retained_size(package.name)
            for package in installed_set.packages.values()
        }
    else:
        display_package_sizes = package_sizes

    colouring = heatmap_colouring(
        0,
        max_size,
        [(0.5, 0.5, 1.0), (1.0, 1.0, 1.0), (0.9, 0.9, 0.5), (1.0, 0.5, 0.5)],
    )

    print("digraph {", file=output_file)
    print("node [shape=box];", file=output_file)
    print("layout=neato", file=output_file)
    print("overlap=false", file=output_file)
    print("model=subset", file=output_file)
    print(file=output_file)
    print("// Package node definitions", file=output_file)
    print("{", file=output_file)

    for package in installed_set.packages.values():
        if not filter_func(package):
            continue

        size = package_sizes[package.name]
        colour = colouring(size)
        colour = f"#{int(colour[0] * 255):02x}{int(colour[1] * 255):02x}{int(colour[2] * 255):02x}"

        own_size = package.size or 0
        own_size_str = format_size(own_size)

        calc_size = display_package_sizes[package.name]
        calc_size_str = format_size(calc_size)

        details = (
            f"{package.name}\\n{own_size_str}; {size_formatter.name} {calc_size_str}"
        )
        print(
            f'"{package.name}" [label="{details}" style=filled fillcolor="{colour}"]',
            file=output_file,
        )

    print("}", file=output_file)
    print(file=output_file)
    print("// Unknown package nodes", file=output_file)
    print("{", file=output_file)
    print(
        'node [style=filled fillcolor="#000000" fontcolor="#ffffff"]', file=output_file
    )

    for package_name in installed_set.unknowns:
        print(
            f'"{package_name}"',
            file=output_file,
        )

    print("}", file=output_file)
    print(file=output_file)
    print("// Dependency edges", file=output_file)
    print("{", file=output_file)

    for package in installed_set.packages.values():
        if not filter_func(package):
            continue

        for dependency in package.dependencies:
            if dependency in installed_set.packages and not filter_func(
                installed_set.packages[dependency]
            ):
                continue

            print(f'"{package.name}" -> "{dependency}"', file=output_file)

    print("}", file=output_file)

    if include_optional:
        print(file=output_file)
        print("// Optional dependency edges", file=output_file)
        print("{", file=output_file)
        print("edge [style=dashed]", file=output_file)

        for package in installed_set.packages.values():
            if not filter_func(package):
                continue

            for dependency in package.optional_dependencies:
                if dependency in installed_set.packages and not filter_func(
                    installed_set.packages[dependency]
                ):
                    continue

                print(
                    f'"{package.name}" -> "{dependency}"',
                    file=output_file,
                )

        print("}", file=output_file)

    print("}", file=output_file)


def main():
    """Main entry point; parses pacman output and prints a graph of the packages."""

    package_filters = {
        "no-deps": (lambda _: lambda package: not package.dependencies),
        "no-revdeps": (
            lambda installed_set: lambda package: package.name
            not in installed_set.revdep_cache
        ),
        "no-optional-deps": (
            lambda _: lambda package: not package.optional_dependencies
        ),
    }

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate a graph of pacman packages.")
    parser.add_argument(
        "--optional",
        action="store_true",
        help="Include optional dependencies in the graph",
    )
    parser.add_argument(
        "--size-type",
        type=str,
        choices=[
            "own",
            "retained",
            "adjusted",
            "uniquely_retained",
            "retained_packages",
        ],
        default="own",
        help="Size type to use for the graph",
    )
    parser.add_argument(
        "--filter",
        action="append",
        choices=package_filters.keys(),
        help="Filter packages to display in the graph. May be used multiple times, in which case all specified filters are applied.",
    )
    args = parser.parse_args()

    if args.size_type == "own":
        size_formatter = OwnSizeFormatter()
    elif args.size_type == "retained":
        size_formatter = RetainedSizeFormatter()
    elif args.size_type == "adjusted":
        size_formatter = AdjustedSizeFormatter()
    elif args.size_type == "uniquely_retained":
        size_formatter = UniquelyRetainedSizeFormatter()
    elif args.size_type == "retained_packages":
        size_formatter = RetainedPackagesFormatter()
    else:
        raise ValueError(f"Unknown size type {args.size_type}")

    installed_set = PacmanInstalledSet.retrieve_pacman_packages()
    filters = [
        package_filters[filter_name](installed_set) for filter_name in args.filter or []
    ]
    overall_filter_func = None

    def filter_and(f1, f2):
        return lambda package: f1(package) and f2(package)

    for filter_func in filters:
        if overall_filter_func is None:
            overall_filter_func = filter_func
        else:
            overall_filter_func = filter_and(overall_filter_func, filter_func)

    make_graph(
        installed_set,
        size_formatter,
        sys.stdout,
        filter_func=overall_filter_func,
        include_optional=args.optional,
    )


if __name__ == "__main__":
    main()
