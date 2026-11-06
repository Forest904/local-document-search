"""Avvio tracciabile del desktop; nessun server o secondo backend."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-file", type=Path, required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--spawn", action="store_true")
    args = parser.parse_args()
    if args.spawn:
        # Non eredita le pipe del task/terminale: il task termina anche con GUI aperta.
        runtime = args.session_file.parent
        with (runtime / "desktop-stdout.log").open("w") as output, (runtime / "desktop-stderr.log").open("w") as errors:
            process = subprocess.Popen(
                [str(Path(sys.executable).with_name("pythonw.exe")), str(Path(__file__).resolve()),
                 "--session-file", str(args.session_file), "--token", args.token],
                stdin=subprocess.DEVNULL, stdout=output, stderr=errors, close_fds=True,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            )
        print(process.pid)
        return 0
    record = {"pid": os.getpid(), "token": args.token}
    temporary = args.session_file.with_suffix(".tmp")
    temporary.write_text(json.dumps(record), encoding="utf-8")
    temporary.replace(args.session_file)
    try:
        from local_document_search_desktop.main import main
        sys.argv = [sys.argv[0]]
        return main()
    finally:
        try:
            if json.loads(args.session_file.read_text(encoding="utf-8")) == record:
                args.session_file.unlink()
        except (OSError, ValueError):
            pass


if __name__ == "__main__":
    sys.exit(run())
