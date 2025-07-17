import cProfile
import io
from datetime import datetime
from pathlib import Path
from pstats import SortKey, Stats


class MoccasinProfiler:
    """
    A class to handle profiling of the Moccasin CLI.
    It uses cProfile to profile main commands and provides a way to save and analyze the profiling data.
    """

    MAX_PRINT_LINES = 10

    def __init__(self, argv: list[str]):
        self.pr = cProfile.Profile()
        self.io = io.StringIO()
        self.report_path = Path(__file__).parent / "reports"
        self.argv = argv

    def __enter__(self):
        """
        Start profiling when entering the context.
        """
        print("[Profiling] Starting profiling for: mox ", *self.argv)
        self.pr.enable()

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Stop profiling when exiting the context and save the profiling data.
        """
        self.pr.disable()
        ps = Stats(self.pr, stream=self.io)
        timestamp = datetime.now().strftime("%Y-%m-%d")
        self._write_report_header(timestamp)
        self._write_stats_sections(ps)
        print(self.io.getvalue())
        self._save_reports(timestamp)
        print("[Profiling] Profiling completed for: mox ", *self.argv)

    def _write_report_header(self, timestamp: str):
        """
        Write the header section of the profiling report, including arguments and timestamp.
        """
        self.io.write("=== Moccasin CLI Profiling Report ===\n\n")
        self.io.write(f"Command: {' '.join(self.argv)}\n")
        self.io.write(f"Profiling report generated at {timestamp}\n\n")

    def _write_stats_sections(self, ps: Stats):
        """
        Write the profiling statistics sections (cumulative, time, and function calls) to the report.
        """
        ps.sort_stats(SortKey.CUMULATIVE).strip_dirs().print_stats(self.MAX_PRINT_LINES)

    def _save_reports(self, timestamp: str):
        """
        Save the profiling report and raw profile data to files in the report directory.
        """
        profile_file = self.report_path / f"moccasin_profile_{timestamp}.stats"
        self.pr.dump_stats(profile_file)
        print(f"Profiling data saved to {profile_file}.\n")
        print(
            "You can analyze it with 'uv run snakeviz' or 'uv run python -m pstats'.\n"
        )


# @TODO Implement main function with arg to pass a custom command for profiling
