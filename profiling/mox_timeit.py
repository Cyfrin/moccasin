import os
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from timeit import Timer

from rich import box
from rich.console import Console
from rich.table import Table

from profiling.constants import CLI_COMMANDS, MOCK_PROJECT


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


def print_results_table(results: list, number: int):
    """Print the results in a formatted table.

    :param results: The list of results to print.
    :param number: The number of runs for each command.
    """
    console = Console()
    table = Table(title="Mox CLI Timeit Results", box=box.MARKDOWN)
    table.add_column("Command")
    for i in range(number):
        table.add_column(f"Run {i + 1}", justify="right")

    for res in results:
        row = [res["command"]]
        for t in res["times"]:
            if t == float("inf"):
                cell = "ERR"
            else:
                cell = f"{t:.4f}"
            row.append(cell)
        table.add_row(*row)
    console.print(table)


def mox_cli_timeit(number=5):
    """Time the execution of a command using the mox CLI in a temp directory.

    This function sets up a temporary directory, copies the mock project files,
    and executes the specified CLI commands multiple times to gather timing data.

    :param number: The number of times to execute each command for timing.
    """
    results = []
    with TemporaryDirectory() as tmp_dir:
        shutil.copytree(MOCK_PROJECT, Path(tmp_dir), dirs_exist_ok=True)
        current_dir = Path.cwd()
        try:
            os.chdir(tmp_dir)
            for command in CLI_COMMANDS:
                res = timeit_command(command, number)
                results.append(res)
        finally:
            os.chdir(current_dir)
    print_results_table(results, number)


def main():
    mox_cli_timeit()


if __name__ == "__main__":
    main()

# @TODO Add optionnal arg to pass a custom command for profiling
# @TODO Maybe use IO to capture table output to store in a file under reports/
