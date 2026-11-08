"""Entry point standalone e diagnostica esplicita del pacchetto."""
from pathlib import Path
import argparse
import cProfile
import concurrent.futures
import importlib.metadata
import math
import os
import platform
import pstats
import random
import runpy
import shutil
import statistics
import subprocess
import sys
import tempfile
import textwrap
import unittest.mock

from local_document_search_desktop.main import main


def dispatch():
    if len(sys.argv) > 1 and sys.argv[1] in ("--diagnostic", "--diagnostic-phase"):
        scripts = Path(sys.executable).parent / "diagnostics"
        sys.path.insert(0, str(scripts))
        runner = scripts / "run_v2_benchmark.py"
        if not runner.is_file():
            raise RuntimeError("Diagnostica assente dal payload")
        packaged_run = sys.argv[1] == "--diagnostic"
        os.environ["LDS_PACKAGED_DIAGNOSTIC"] = "1"
        sys.argv = [str(runner), "run" if packaged_run else "_phase", *sys.argv[2:]]
        if packaged_run:
            sys.argv.extend(["--payload-manifest", str(Path(sys.executable).parent / "BUILD-MANIFEST.json")])
        runpy.run_path(str(runner), run_name="__main__")
        return 0
    return main()


if __name__ == "__main__":
    raise SystemExit(dispatch())
