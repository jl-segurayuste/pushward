# pushward

Escáner de secretos y datos reales antes de que lleguen a un repositorio —
pensado para engancharse como hook `pre-push`, no solo como auditoría puntual.

```
$ pushward scan .

pushward — /ruta/al/repo

── secrets ──────────────────────────────
  40 fichero(s) analizados, 1 hallazgo(s).
  [HIGH  ] Posible secreto: Clave privada (PEM) (deploy/id_rsa:1)
           Revisar y revocar si es real antes de publicar.

── watchlist ────────────────────────────
  3 entrada(s) en la watchlist, 40 fichero(s) analizados, 1 hallazgo(s).
  [HIGH  ] Entrada de watchlist encontrada: 'Consum' (docs/notas.md:12)

Total: 2 hallazgo(s) — 2 high
```

## Por qué existe

Los escáneres de secretos habituales (git-secrets, gitleaks...) casan patrones:
claves con forma de clave, tokens con forma de token. Pero la fuga más
frecuente en la práctica no tiene "forma" reconocible por regex — es una IP
interna real, el nombre de un cliente, el de un empleado, o un DNI de verdad
colado como "ejemplo". Ningún escáner por patrones puede distinguir eso de un
valor inventado, porque no sabe qué es real. `pushward` sí puede, porque tú se
lo dices una vez (la `watchlist`) y lo comprueba en todos tus repos, para
siempre.

## Instalación

Todavía no está en PyPI:

```bash
pip install git+https://github.com/jl-segurayuste/pushward.git
```

## Uso

```bash
pushward scan .                         # informe en consola
pushward scan . --staged                # solo lo que hay en stage (usado por el hook)
pushward scan . --json
pushward scan . --fail-on high          # código de salida 1 si hay algo "high"
pushward list-checks

pushward install-hook .                 # instala un hook pre-push en este repo
pushward uninstall-hook .

pushward watchlist add "Nombre Real"    # nunca se commitea: vive en ~/.config/pushward/
pushward watchlist list
pushward watchlist remove "Nombre Real"
```

## Checks incluidos

| Check | Qué detecta |
|---|---|
| `secrets` | Claves privadas, tokens AWS/GitHub/Slack/OpenAI, JWT, asignaciones de credenciales en claro |
| `private_ips` | IPs de rangos privados (10.x, 172.16-31.x, 192.168.x) |
| `watchlist` | Nombres/empresas/dominios reales que tú has marcado como "nunca en un repo" |
| `dni_pattern` | DNI/NIE español con dígito de control válido (no marca placeholders tipo `12345678A`) |
| `sensitive_filenames` | Nombres de fichero (PDF/DOCX/XLSX) que sugieren contenido personal, sin abrir el contenido |

Ninguno ejecuta el código del repo analizado. Cada check es un plugin
independiente (`importlib.metadata.entry_points`, grupo `pushward.checks`) —
añadir uno nuevo no toca el núcleo.

## La watchlist

Vive fuera de cualquier repo, en `~/.config/pushward/watchlist.txt` —
justo porque el propio fichero contendría los nombres que quieres proteger,
así que no tiene sentido que viva dentro de un repo que podrías publicar.
Casa variantes de mayúsculas y separador (`Ruben.Blanco` == `ruben_blanco` ==
`RubenBlanco`), con límites de palabra para no marcar falsos positivos como
"Consum" dentro de "consumo".

## Desarrollo

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para añadir un check nuevo.
