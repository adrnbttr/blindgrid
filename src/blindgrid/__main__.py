"""Entry point for ``python -m blindgrid``.

The installed ``blindgrid`` command is the normal way in. This exists for
environments where a pip-installed script does not land on the PATH — the iOS
shells are the usual case — so the tool is still reachable there.
"""

from __future__ import annotations

from blindgrid.cli import app

if __name__ == "__main__":
    app()
