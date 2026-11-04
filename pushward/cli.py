from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from pushward import hook, watchlist_store
from pushward.plugin import SEVERITIES
from pushward.report import build_report, write_json
from pushward.runner import discover_checks, run_checks
from pushward.scanner import ZERO_OID, ScanError, commits_to_push, materialize_commits

_SEVERITY_ORDER = {sev: idx for idx, sev in enumerate(SEVERITIES)}


def _cmd_scan(args: argparse.Namespace) -> int:
    repo_path = Path(args.path).resolve()
    only = set(args.only) if args.only else None
    skip = set(args.skip) if args.skip else None

    results = run_checks(repo_path, staged=args.staged, only=only, skip=skip)
    report = build_report(repo_path, results)

    if args.json:
        print(write_json(report))
    else:
        print(report.to_console())

    # Un check que revienta deja el análisis incompleto: antes solo se avisaba y salía 0 (o 1 según
    # --fail-on), y en un CI pasaba por verde sin haber mirado lo que ese check mira.
    failed = [r.check_name for r in results if r.error]
    if failed:
        print(f"error: no se pudieron ejecutar: {', '.join(failed)} (análisis incompleto)", file=sys.stderr)
        return 2

    if args.fail_on:
        worst = report.worst_severity()
        if worst is not None and _SEVERITY_ORDER[worst] >= _SEVERITY_ORDER[args.fail_on]:
            return 1
    return 0


def _cmd_pre_push_hook(args: argparse.Namespace) -> int:
    """Invocado por el hook instalado. Git pasa por stdin una línea por ref
    que se va a empujar: "<local ref> <local oid> <remote ref> <remote oid>".
    Se escanea el contenido de cada commit que se sube, no el árbol de trabajo.
    """
    repo_path = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="pushward-") as tmp:
        root = Path(tmp)
        files: list[Path] = []
        for line in sys.stdin:
            parts = line.split()
            if len(parts) != 4:
                continue
            _local_ref, local_oid, _remote_ref, remote_oid = parts
            if local_oid == ZERO_OID:
                continue  # se está borrando una rama, nada que subir
            try:
                commits = commits_to_push(repo_path, local_oid, remote_oid)
                files.extend(materialize_commits(repo_path, commits, root))
            except ScanError as exc:
                print(f"pushward: no se pudo revisar el push, se bloquea: {exc}", file=sys.stderr)
                return 1

        if not files:
            return 0

        results = run_checks(root, files=files)
        report = build_report(repo_path, results)
        print(report.to_console())

    if any(r.error for r in results):
        print("pushward: algún check falló al ejecutarse; se bloquea el push.", file=sys.stderr)
        return 1
    worst = report.worst_severity()
    if worst is not None and _SEVERITY_ORDER[worst] >= _SEVERITY_ORDER["high"]:
        return 1
    return 0


def _cmd_list_checks(args: argparse.Namespace) -> int:
    for name, cls in sorted(discover_checks().items()):
        doc = (cls.__doc__ or "").strip().splitlines()[0] if cls.__doc__ else ""
        print(f"{name}: {doc}")
    return 0


def _cmd_install_hook(args: argparse.Namespace) -> int:
    repo_path = Path(args.path).resolve()
    try:
        target = hook.install(repo_path)
    except FileExistsError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Hook instalado: {target}")
    return 0


def _cmd_uninstall_hook(args: argparse.Namespace) -> int:
    repo_path = Path(args.path).resolve()
    if hook.uninstall(repo_path):
        print("Hook desinstalado.")
        return 0
    print("No había ningún hook de pushward instalado.")
    return 0


def _cmd_watchlist(args: argparse.Namespace) -> int:
    path = watchlist_store.WATCHLIST_PATH
    if args.watchlist_action == "add":
        watchlist_store.add_entry(args.value, path=path)
        print(f"Añadido a la watchlist: {args.value!r}")
    elif args.watchlist_action == "remove":
        removed = watchlist_store.remove_entry(args.value, path=path)
        print("Eliminado." if removed else "No estaba en la watchlist.")
    elif args.watchlist_action == "list":
        entries = watchlist_store.load_entries(path)
        if not entries:
            print("La watchlist está vacía.")
        for entry in entries:
            print(entry)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pushward")
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("scan", help="Analiza un repo en busca de secretos/datos reales")
    p_scan.add_argument("path", nargs="?", default=".")
    p_scan.add_argument("--staged", action="store_true", help="Solo ficheros en stage (para el hook)")
    p_scan.add_argument("--only", action="append", help="Ejecutar solo este check (repetible)")
    p_scan.add_argument("--skip", action="append", help="Saltar este check (repetible)")
    p_scan.add_argument("--json", action="store_true")
    p_scan.add_argument("--fail-on", choices=SEVERITIES, default=None)
    p_scan.set_defaults(func=_cmd_scan)

    p_hook = sub.add_parser("pre-push-hook", help="Invocado por el hook instalado (lee refs de stdin)")
    p_hook.set_defaults(func=_cmd_pre_push_hook)

    p_list = sub.add_parser("list-checks", help="Lista los checks instalados")
    p_list.set_defaults(func=_cmd_list_checks)

    p_install = sub.add_parser("install-hook", help="Instala el hook pre-push")
    p_install.add_argument("path", nargs="?", default=".")
    p_install.set_defaults(func=_cmd_install_hook)

    p_uninstall = sub.add_parser("uninstall-hook", help="Quita el hook pre-push")
    p_uninstall.add_argument("path", nargs="?", default=".")
    p_uninstall.set_defaults(func=_cmd_uninstall_hook)

    p_watchlist = sub.add_parser("watchlist", help="Gestiona la watchlist global")
    wl_sub = p_watchlist.add_subparsers(dest="watchlist_action", required=True)
    wl_add = wl_sub.add_parser("add")
    wl_add.add_argument("value")
    wl_remove = wl_sub.add_parser("remove")
    wl_remove.add_argument("value")
    wl_sub.add_parser("list")
    p_watchlist.set_defaults(func=_cmd_watchlist)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
