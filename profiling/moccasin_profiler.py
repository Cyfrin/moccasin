import cProfile
import io
from datetime import datetime
from pathlib import Path
from pstats import SortKey, Stats


class MoccasinProfiler:
    """A context manager to handle profiling of the Moccasin CLI using cProfile."""

    MAX_PRINT_LINES = 25

    def __init__(self, log_dir=None):
        self.log_dir = Path(log_dir) if log_dir else Path(__file__).parent / "reports"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.stats_file = self.log_dir / "mox_profiling.stats"
        self.log_file = self.log_dir / "mox_profiling.log"
        self.pr = None
        self.io_stream = None

    def save_stats(self, pr: cProfile.Profile):
        """Save the profiling stats to a file."""
        pr.dump_stats(self.stats_file)
        print(f"[INFO] Stats file saved as {self.stats_file}")

    def save_log(self, pr: cProfile.Profile, io_stream: io.StringIO, cmdline: str):
        """Save the profiling log to a file.

        :param pr: The cProfile.Profile instance.
        :param io_stream: The StringIO stream to capture profiling output.
        :param cmdline: The command line used to invoke the CLI.
        """
        ps = Stats(pr, stream=io_stream)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        io_stream.write("=== Moccasin CLI Profiling Report ===\n\n")
        io_stream.write(f"Command line: {cmdline}\n")
        io_stream.write(f"Profiling report generated at {timestamp}\n\n")
        # Sort by time then cumulative time
        ps.strip_dirs().sort_stats(SortKey.TIME, SortKey.CUMULATIVE).print_stats(
            self.MAX_PRINT_LINES
        )
        print(io_stream.getvalue())
        with open(self.log_file, "a") as f:
            f.write("=========================================================" + "\n")
            f.write(f"\n=== Mox CLI Profiling Results - {timestamp} ===\n\n")
            f.write(f"Command line: {cmdline}\n\n")
            f.write("Profiling Output:\n\n")
            f.write(io_stream.getvalue())
        print(f"[INFO] Profiling output saved to {self.log_file}")

    def __enter__(self):
        """Start profiling when entering the context."""
        self.pr = cProfile.Profile()
        self.io_stream = io.StringIO()
        self.pr.enable()
        print("[Profiling] Starting profiling")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop profiling when exiting the context and save the profiling data."""
        import sys

        self.pr.disable()
        print("[Profiling] Profiling completed")
        # Log the command line used for the CLI run
        cmdline = " ".join(sys.argv)
        self.save_stats(self.pr)
        self.save_log(self.pr, self.io_stream, cmdline)
        return False
