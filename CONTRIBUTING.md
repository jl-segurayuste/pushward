# Contribuir

## Añadir un check nuevo

Cada check implementa el protocolo `Check` (`pushward/plugin.py`):

```python
class MiCheck:
    name = "mi_check"

    def run(self, files: list[Path], repo_path: Path) -> CheckResult:
        ...
```

`files` ya viene filtrado por `git ls-files` (o el diff en stage si se llamó
con `--staged`) — no hay que reimplementar el descubrimiento de ficheros.

Se registra vía entry point en tu propio `pyproject.toml`:

```toml
[project.entry-points."pushward.checks"]
mi_check = "mi_paquete.check:MiCheck"
```

No hace falta tocar el núcleo de `pushward` para que se descubra —
`pushward list-checks` lo mostrará en cuanto el paquete esté instalado.

## Antes de un PR

- `ruff check .` y `pytest` en verde.
- Todo check nuevo necesita tests, incluidos los casos de falso positivo
  esperado (si tu heurística puede confundirse con datos de ejemplo,
  documéntalo explícitamente en el `detail` del `Finding`).
- Ningún check debe ejecutar código del repo analizado ni abrir el contenido
  de ficheros binarios grandes sin buena razón.
- Cambios en el núcleo (`plugin.py`, `runner.py`, `scanner.py`, `hook.py`)
  se discuten primero en un issue.
