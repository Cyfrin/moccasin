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

### 2. Profile a CLI Command in a Temporary Directory

Use `mox_profiling.py` to run and profile any `mox` CLI command in a temporary directory with a mock project tree:

```sh
python profiling/mox_profiling.py --command "compile"
```

```console
=========================================================

=== Mox CLI Profiling Results - 2025-07-18_13-11-13 ===

Command line: /home/s3bc40/gh-projects/moccasin/.venv/bin/mox compile --profile --quiet

Profiling Output:

=== Moccasin CLI Profiling Report ===

Command line: /home/s3bc40/gh-projects/moccasin/.venv/bin/mox compile --profile --quiet
Profiling report generated at 2025-07-18_13-11-13

         2138731 function calls (2039596 primitive calls) in 4.099 seconds

   Ordered by: internal time, cumulative time
   List reduced from 6414 to 25 due to restriction <25>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
     2182    2.325    0.001    2.325    0.001 {built-in method time.sleep}
    15317    0.347    0.000    0.462    0.000 optimized_field_elements.py:280(__mul__)
     1107    0.070    0.000    0.070    0.000 {built-in method marshal.loads}
        4    0.062    0.015    0.062    0.015 {method 'poll' of 'select.poll' objects}
   1751/6    0.056    0.000    1.559    0.260 {built-in method builtins.exec}
    38308    0.052    0.000    0.086    0.000 optimized_field_elements.py:82(__mul__)
 31710/28    0.036    0.000    0.088    0.003 copy.py:128(deepcopy)
    15434    0.035    0.000    0.056    0.000 optimized_field_elements.py:235(__init__)
      935    0.034    0.000    0.034    0.000 {built-in method builtins.compile}
2571/2508    0.029    0.000    0.214    0.000 {built-in method builtins.__build_class__}
    49566    0.028    0.000    0.039    0.000 optimized_field_elements.py:57(__init__)
320703/320687    0.028    0.000    0.031    0.000 {built-in method builtins.isinstance}
        1    0.024    0.024    0.024    0.024 {method 'load_verify_locations' of '_ssl._SSLContext' objects}
    15317    0.021    0.000    0.021    0.000 optimized_field_elements.py:296(<listcomp>)
     5013    0.020    0.000    0.020    0.000 {built-in method posix.stat}
 1166/178    0.019    0.000    0.045    0.000 _parser.py:516(_parse)
6899/5132    0.017    0.000    0.037    0.000 {built-in method __new__ of type object at 0x5d7a18a85b50}
   120442    0.015    0.000    0.015    0.000 optimized_field_elements.py:247(<genexpr>)
     1107    0.013    0.000    0.013    0.000 {built-in method io.open_code}
     1451    0.012    0.000    0.052    0.000 <frozen importlib._bootstrap_external>:1607(find_spec)
        1    0.012    0.012    2.376    2.376 compile.py:89(compile_project)
105417/81271    0.012    0.000    0.119    0.000 {built-in method builtins.hasattr}
3013/2095    0.012    0.000    0.076    0.000 copy.py:259(_reconstruct)
     1765    0.011    0.000    0.019    0.000 enum.py:242(__set_name__)
       32    0.011    0.000    0.011    0.000 {built-in method posix.waitpid}


=========================================================

```

- This will run `mox compile` in a temp dir, profile the run, and save results to `profiling/reports/`.
- The command is always profiled (no need for a `--profile` flag).
- You can use any valid mox command, e.g.:
  ```sh
  python profiling/mox_profiling.py --command "deploy MyContract"
  ```

### 3. Profile the Main CLI (Advanced)

You can also profile the CLI by running it with the `--profile` flag:

```sh
moccasin --profile <other-args>
```

- This will profile the full CLI process and save results to `profiling/reports/`.
- The profiling context is managed by `MoccasinProfiler`.

> ⚠️ If you run it on your own, it will not use the mock project tree, so ensure you have a valid project structure in the current directory.

## Output

- **profiling/reports/mox_profiling.stats**: Raw cProfile stats (for use with `snakeviz`, `gprof2dot`, etc.)
- **profiling/reports/mox_profiling.log**: Human-readable summary of the top functions by time and cumulative time.

## Custom Profiling

You can use the `MoccasinProfiler` context manager in your own scripts:

```python
from profiling.moccasin_profiler import MoccasinProfiler

with MoccasinProfiler():
    # Your code here
    ...
```

---

For more details, see the code in `mox_profiling.py` and `moccasin_profiler.py`.
