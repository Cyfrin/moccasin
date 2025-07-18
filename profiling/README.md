# Moccasin Profiling Tools

This directory contains tools and helpers for profiling the Moccasin CLI and its commands. The profiling system is designed to make it easy to benchmark and analyze the performance of CLI commands in a reproducible, isolated environment.

## Quick Start

### 1. Benchmark CLI Commands with Timeit

Use `mox_timeit.py` to benchmark the execution time of one or more `mox` CLI commands in a temporary directory with a mock project tree:

```sh
python profiling/mox_timeit.py
```

```console
=========================================================

=== Mox CLI Timeit Results - 2025-07-18 10:18:56 ===

Command                                       | Run 1  | Run 2  | Run 3  | Run 4  | Run 5
----------------------------------------------+--------+--------+--------+--------+-------
install                                       | 0.9675 | 0.9917 | 1.0057 | 1.8051 | 0.9984
compile                                       | 5.1777 | 2.0217 | 2.0189 | 2.1909 | 2.7140
run deploy                                    | 2.1515 | 1.9939 | 1.8852 | 1.9793 | 1.9569
inspect src/decentralized_stable_coin methods | 1.2172 | 1.1502 | 1.1683 | 1.1777 | 1.1739
utils zero                                    | 0.5646 | 0.5644 | 0.5647 | 0.5630 | 0.5602
=========================================================
```

- This will run each command (e.g. `mox compile`, `mox test`) 5 times in a temp dir and print/save a timing table.
- By default, it uses a set of standard commands, but you can provide your own with `--commands` (comma or semicolon separated).
- All runs are isolated and reproducible.

Example:

```sh
python profiling/mox_timeit.py --number 3 --commands "compile;deploy MyContract"
```

Output is saved to `profiling/reports/mox_timeit.log` as a clean, aligned table.

```console
=== Mox CLI Timeit Results - 2025-07-18 19:33:05 ===

Command              | Run 1  | Run 2  | Run 3
---------------------+--------+--------+-------
install              | 1.0665 | 0.9258 | 1.0136
compile --no-install | 4.5361 | 2.0332 | 1.8549
run deploy           | 2.1196 | 2.7561 | 1.8999
=========================================================
```

### 2. Profile a CLI Command in a Temporary Directory

Use `mox_profiling.py` to run and profile any `mox` CLI command in a temporary directory with a mock project tree:

```sh
python profiling/mox_profiling.py --command "compile"
```

```console
=========================================================

=== Mox CLI Profiling Results - 2025-07-18_19-26-16 ===

Command line: /home/s3bc40/gh-projects/moccasin/.venv/bin/mox compile --quiet

Profiling Output:

=== Moccasin CLI Profiling Report ===

Command line: /home/s3bc40/gh-projects/moccasin/.venv/bin/mox compile --quiet
Profiling report generated at 2025-07-18_19-26-16

         2169412 function calls (2070359 primitive calls) in 8.762 seconds

   Ordered by: internal time, cumulative time
   List reduced from 6318 to 25 due to restriction <25>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
     6171    6.907    0.001    6.907    0.001 {built-in method time.sleep}
    15317    0.312    0.000    0.417    0.000 optimized_field_elements.py:280(__mul__)
        1    0.126    0.126    7.147    7.147 compile.py:89(compile_project)
     1107    0.072    0.000    0.072    0.000 {built-in method marshal.loads}
   1751/6    0.059    0.000    1.533    0.255 {built-in method builtins.exec}
    23422    0.052    0.000    0.070    0.000 pool.py:756(ready)
    38308    0.051    0.000    0.084    0.000 optimized_field_elements.py:82(__mul__)
 31710/28    0.036    0.000    0.087    0.003 copy.py:128(deepcopy)
      935    0.034    0.000    0.034    0.000 {built-in method builtins.compile}
    15434    0.031    0.000    0.051    0.000 optimized_field_elements.py:235(__init__)
2571/2508    0.029    0.000    0.218    0.000 {built-in method builtins.__build_class__}
319032/319016    0.027    0.000    0.030    0.000 {built-in method builtins.isinstance}
    49566    0.027    0.000    0.038    0.000 optimized_field_elements.py:57(__init__)
        1    0.025    0.025    0.025    0.025 {method 'load_verify_locations' of '_ssl._SSLContext' objects}
    15317    0.020    0.000    0.020    0.000 optimized_field_elements.py:296(<listcomp>)
     4693    0.019    0.000    0.019    0.000 {built-in method posix.stat}
 1151/168    0.019    0.000    0.046    0.000 _parser.py:516(_parse)
6898/5131    0.018    0.000    0.038    0.000 {built-in method __new__ of type object at 0x6528b526ab50}
    23433    0.017    0.000    0.017    0.000 threading.py:575(is_set)
    79228    0.017    0.000    0.017    0.000 {method 'append' of 'list' objects}
100335/98168    0.015    0.000    0.016    0.000 {built-in method builtins.len}
   120442    0.014    0.000    0.014    0.000 optimized_field_elements.py:247(<genexpr>)
     1107    0.013    0.000    0.013    0.000 {built-in method io.open_code}
     1451    0.012    0.000    0.053    0.000 <frozen importlib._bootstrap_external>:1607(find_spec)
     1765    0.012    0.000    0.020    0.000 enum.py:242(__set_name__)

```

- This will run `mox compile` in a temp dir, profile the run, and save results to `profiling/reports/`.
- The command is always profiled (no need for a `--profile` flag).
- You can use any valid mox command, e.g.:
  ```sh
  python profiling/mox_profiling.py --command "deploy MyContract"
  ```

Behind the scenes, `moccasin_profiling.py` will set the `MOX_PROFILE` environment variable to `1` before running the command, which enables profiling in the Moccasin CLI. In the `__main__.py` file, the `MoccasinProfiler` context manager is used to wrap the command execution, capturing profiling data.

## Output

**For profiling/mox_timeit.py:**

- **profiling/reports/mox_timeit.log**: A clean, aligned table of command execution times across multiple runs.

**For profiling/mox_profiling.py:**

- **profiling/reports/mox_profiling.stats**: Raw cProfile stats (for use with `snakeviz`, `pstats`, etc.)
- **profiling/reports/mox_profiling.log**: Human-readable summary of the top functions by time and cumulative time.

To read the profiling stats, you can use `pstats` in the terminal:

```sh
python -m pstats profiling/reports/mox_profiling.stats
```

You can also visualize the profiling data using tools like `snakeviz`:

```sh
# Install snakeviz in its own venv
uv add tool snakeviz
# Then visualize the profiling stats
snakeviz profiling/reports/mox_profiling.stats
```

---

For more details, see the code in `mox_profiling.py` and `moccasin_profiler.py`.
