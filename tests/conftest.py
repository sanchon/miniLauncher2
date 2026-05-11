"""Fixtures compartidos para toda la suite de tests."""
import pytest
from click.testing import CliRunner
from pathlib import Path
from launcher import load_config

# INI mínimo con un comando por cada modo y variantes de parámetros.
# Independiente de commands.ini para que los tests no cambien al editar ese fichero.
MINI_INI = """\
[mini-launcher]
browser_executable =
browser_arguments =

[deploy]
description = Despliega una version en un entorno
mode = shell
template = echo Desplegando entorno={env} version={version}
params = env, version
required = env, version
env.choices = dev, staging, prod

[buscar]
description = Abre una busqueda en el navegador
mode = browser
template = https://www.google.com/search?q={termino}
params = termino
required = termino

[abrir]
description = Abre fichero con la app asociada
mode = open
template = {ruta}
params = ruta
required = ruta
ruta.path = true

[git_log]
description = Ultimas confirmaciones de git
mode = exec
executable = git
arguments = log -n {n} --oneline
params = n
required = n
n.choices = 1, 3, 5

[sin_descripcion]
mode = shell
template = echo hola

[editor]
description = Abre un fichero en el editor (segundo plano)
mode = exec
executable = code
arguments = {fichero}
detach = true
params = fichero
required = fichero
fichero.path = true

[buscar_chrome]
description = Busca en Google con un navegador concreto
mode = browser
template = https://www.google.com/search?q={q}
executable = /usr/bin/google-chrome
arguments = {url}
params = q
required = q
"""


@pytest.fixture
def ini_path(tmp_path: Path) -> Path:
    """Fichero INI temporal con el conjunto de comandos de prueba."""
    p = tmp_path / "commands.ini"
    p.write_text(MINI_INI, encoding="utf-8")
    return p


@pytest.fixture
def cfg(ini_path: Path) -> dict:
    """Configuración cargada desde el INI temporal."""
    return load_config(ini_path)


@pytest.fixture
def runner() -> CliRunner:
    """CliRunner de Click para invocar main() en proceso sin subproceso."""
    return CliRunner()
