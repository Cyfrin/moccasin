import os
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from timeit import Timer

from profiling.constants import CLI_COMMANDS, MOCK_PROJECT


def parse_args():
    """Parse command line arguments for the mox CLI timeit script."""
    import argparse

    parser = argparse.ArgumentParser(description="Profile mox CLI commands.")
    parser.add_argument(
        "--number", type=int, default=5, help="Number of runs per command"
    )
    parser.add_argument(
        "--commands",
        type=str,
        default=None,
        help="Custom commands (comma or semicolon separated)",
    )
    return parser.parse_args()


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a command in the mox CLI environment.

    :param cmd: The command to run as a list of strings.
    :return: The result of the command execution.
    """
    cmd = ["mox"] + cmd
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return result


def timeit_command(command: str, number: int) -> dict:
    """Time the execution of a command using the mox CLI.

    :param command: The command to execute.
    :param number: The number of times to execute the command for timing.
    :return: A dictionary containing the command, execution times, and errors.
    """
    times = []
    errors = []

    def timed():
        """Function to time the command execution."""
        try:
            run_cmd(command.split())
            return 0  # dummy return, not used
        except subprocess.CalledProcessError as e:
            raise e

    timer = Timer(timed)
    # Repeat the command execution to get timing results
    try:
        rep_times = timer.repeat(repeat=number, number=1)
        times = rep_times
        errors = ["" for _ in rep_times]
    except subprocess.CalledProcessError as e:
        times = [float("inf")] * number
        errors = [str(e)] * number
    return {"command": command, "times": times, "errors": errors}


def build_aligned_table(results: list, number: int) -> str:
    """Build a clean, aligned table as a string.

    :param results: List of dictionaries containing command results.
    :param number: Number of runs per command.
    """
    header = ["Command"] + [f"Run {i + 1}" for i in range(number)]
    rows = []
    for res in results:
        row = [res["command"]]
        for t in res["times"]:
            if t == float("inf"):
                cell = "ERR"
            else:
                cell = f"{t:.4f}"
            row.append(cell)
        rows.append(row)
    cols = [header] + rows
    col_widths = [max(len(str(col[i])) for col in cols) for i in range(len(header))]

    def fmt_row(row):
        return " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))

    lines = [fmt_row(header), "-+-".join("-" * w for w in col_widths)]
    for row in rows:
        lines.append(fmt_row(row))
    return "\n".join(lines)


def save_aligned_table(table_str: str):
    """Save the aligned table to a log file in reports/profiling with a timestamp.

    :param table_str: The aligned table string to save.
    """
    from datetime import datetime

    log_dir = Path(__file__).parent / "reports"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = log_dir / "mox_timeit.log"
    with open(log_file, "a") as f:
        # Write a header with the timestamp
        f.write("=========================================================\n")
        f.write(f"\n=== Mox CLI Timeit Results - {timestamp} ===\n\n")
        f.write(table_str)
        f.write("\n")
        f.write("=========================================================\n")
    print(f"\n[Log saved to {log_file}]")


def mox_cli_timeit(number=5, custom_commands: str = None):
    """
    Time the execution of a command using the mox CLI in a temp directory.
    If custom_commands is provided (comma or semicolon separated), it takes precedence over CLI_COMMANDS.
    """
    if custom_commands:
        # Split by comma or semicolon, strip whitespace
        commands = [
            cmd.strip()
            for cmd in custom_commands.replace(";", ",").split(",")
            if cmd.strip()
        ]
        print(f"[INFO] Using custom commands: {commands}")
    else:
        commands = CLI_COMMANDS
        print(f"[INFO] Using default CLI_COMMANDS: {commands}")
    print(f"[INFO] Starting CLI profiling with {number} runs per command...")
    results = []
    with TemporaryDirectory() as tmp_dir:
        shutil.copytree(MOCK_PROJECT, Path(tmp_dir), dirs_exist_ok=True)
        current_dir = Path.cwd()
        try:
            os.chdir(tmp_dir)
            for idx, command in enumerate(commands, 1):
                print(f"[RUN {idx}/{len(commands)}] Profiling: mox {command}")
                res = timeit_command(command, number)
                results.append(res)
                print(f"[DONE] {command}")
        finally:
            os.chdir(current_dir)
    print("[INFO] Profiling complete. Building results table...")
    table_str = build_aligned_table(results, number)
    print("\nMox CLI Timeit Results (Aligned Table):\n")
    print(table_str)
    save_aligned_table(table_str)


def main():
    args = parse_args()
    mox_cli_timeit(number=args.number, custom_commands=args.commands)


if __name__ == "__main__":
    main()
