# PLAN — Alinear la librería `db` a la normativa de librerías internas

> **Estado al 2026-10-28: F1 a F6 ejecutadas y publicadas.** La versión `v0.2.0`
> está tagueada y publicada en `https://github.com/SebaxFentex/db`. Queda
> pendiente, fuera de esta versión, migrar los proyectos consumidores
> (`python_portaciones`, `python_tabla_calendario`,
> `python_simplificacion_planes`, `python_reportes_interbd`): la ruta editable
> vieja y las llamadas a `run_query` / `*_from_env` siguen rotas en esos
> proyectos hasta que se migren.

Auditoría: 2026-10-28 · Objeto: `D:\Tigo\Proyectos\1. PROPIOS\1.5 - Librerias\db`
Norma que manda: `TIGO_PYTHON_LIBRERIAS.md` (secciones 1 a 12) + `TIGO_GENERAL.md`.
Referencia de casa: `sharepoint` v1.2.1 (única librería ya alineada).

---

## 1. Veredicto

**32 de 54 requisitos no se cumplen**, 1 queda parcial y 1 no se pudo verificar
(los otros 15 cumplen y 5 no aplican).
`db` no es hoy una librería interna: es una carpeta de módulos sueltos que se
importa por estar en el directorio de trabajo. No hay paquete `uv_build`, no hay
layout `src/`, no hay `.venv`, no hay tests, no hay `ejecutables/`, no hay
`AGENTS.md`, no hay `.gitignore` y no es un repositorio git. El `uv.lock` está
desactualizado y los dos consumidores que la declaran apuntan a una ruta que no
existe.

Lo que hay de bueno y se conserva: la versión está en formato `X.Y.Z`, el código
está sin `ñ`, en `snake_case`, sin `load_dotenv`, sin `basicConfig`, sin
`StreamHandler` en módulos, sin symlinks, y no hay carpetas prohibidas
(`Insumos`, `Salidas`, `ETL`, `rutas.py`, `env.py`, `main.py`, `scripts/`,
`dev/`, `querys/`, `utils/`). El núcleo funcional (Oracle, SQL Server, ejecución
con separador) es correcto y es lo único que usan 20 archivos de 4 proyectos
B2B: la reestructura no cambia qué hace, cambia cómo se entrega y cómo recibe
la configuración.

### Bloqueantes P0 (antes que cualquier cosmética)

| # | Bloqueante | Nombre | Evidencia |
|---|---|---|---|
| P0-1 | Lock desactualizado / sin entorno | Reproducibilidad rota: no se puede reconstruir el ambiente | `uv lock --check` → *"The lockfile at `uv.lock` needs to be updated"*; `uv.lock` registra `db 0.1.0` y `pyproject.toml` dice `0.1.1`; no existe `.venv` |
| P0-2 | No es paquete instalable del tipo exigido | Layout y backend: el import depende del directorio de trabajo | Paquete en `db/` de la raíz (no `src/db/`); `[build-system]` con `hatchling` + `[tool.hatch.build.targets.wheel] packages = ["db"]`, no `uv_build` |
| P0-3 | Nadie la consume de verdad | Los consumidores apuntan a una ruta inexistente | `python_portaciones` y `python_reportes_interbd` declaran `db = { path = "../../../../Python/librerias/db", editable = true }`; esa carpeta no existe (la real es `Proyectos/1. PROPIOS/1.5 - Librerias/db`) |
| P0-4 | Sin historial ni publicación | No hay repositorio git ni romoto GitHub, así que no hay tags, release ni forma de rastrear rupturas | `git rev-parse --is-inside-work-tree` → *"not a git repository"* |

---

## 2. Tabla de cumplimiento — sección por sección

### 2.1 Estructura (sección 2)

| Requisito | Estado | Evidencia |
|---|---|---|
| Paquete en `src/<nombre>/` | NO | el paquete vive en `db/` en la raíz |
| `tests/` (con `tests/archivos/` solo si hay fixtures) | NO | no existe `tests/` |
| `ejecutables/` (build, abrir_vscode, tests/) | NO | no existe `ejecutables/`; cero `.bat` en la librería |
| `logs/` (solo si el entrypoint escribe ahí) | NO | no hay logging ni carpeta `logs/` |
| `.env.example` versionado | NO | no existe; tampoco `.env` |
| `.gitignore` en la raíz | NO | no existía en la raíz (el `dist/.gitignore` lo genera `uv build` y no cubre `.venv/`, `.env` ni `logs/`) |
| `.python-version` | SÍ (desalineado) | contiene `3.13`, la casa usa `3.14` |
| `README.md` | SÍ (incompleto) | 116 líneas, cubre 1 de 7 secciones obligatorias (ver 2.7) |
| `AGENTS.md` | NO | no existe |
| Sin carpetas ni archivos prohibidos | SÍ | no hay `Insumos`, `Salidas`, `Documentacion`, `ETL`, `dbeaver`, `rutas.py`, `env.py`, `main.py`, `scripts/`, `dev/`, `querys/`, `utils/` |

### 2.2 Paquete y build (sección 3)

| Requisito | Estado | Evidencia |
|---|---|---|
| `[build-system]` = `uv_build>=0.13.0,<1.0` | NO | `hatchling>=1.24.0` / `hatchling.build` (pyproject líneas 18-23) |
| `.venv` propio | NO | no existe `.venv`; el paquete solo se importa por `cwd` |
| `uv.lock` propio y al día | NO | existe pero `uv lock --check` falla |
| `requires-python >= "3.14"` | NO | `>=3.13` |
| Sin workspace global, venvs compartidos, `UV_PROJECT_ENVIRONMENT`, `PYTHONPYCACHEPREFIX`, `RUFF_CACHE_DIR` | SÍ | grep sin coincidencias en todo el árbol |

### 2.3 Entrypoint (sección 4)

| Requisito | Estado | Evidencia |
|---|---|---|
| `__main__.py` solo si expone comando | N/A | `db` no expone comando; no hay `__main__` |
| Sin `main.py` suelto ni `if __name__ == "__main__"` en módulos | SÍ | grep sin coincidencias |
| `argparse` y precedencia arg > env > error | N/A | no aplica sin comando |

### 2.4 `.env` es del consumidor (sección 5) — la violación central

| Requisito | Estado | Evidencia |
|---|---|---|
| La librería **no** lee variables de entorno para operar | NO | `general.py:10` `SEPARADOR = get_env("DB_SEPARADOR", ...)`; `oracle.py:24-29` `get_required_env("ORACLE_USER"/"_PASSWORD"/"_HOST"/"_SERVICE_NAME")`, `get_typed_env("_PORT")`, `get_env("_X64_PATH")`; `sql_server.py:19-22` `get_required_env(f"{prefix}_USER"/"_PASSWORD"/"_HOST"/"_DB")`; más `_env.py` entero |
| No llama `load_dotenv()` | SÍ | grep sin coincidencias |

Además la librería **hardcodea configuración de negocio de Tigo**: los prefijos
`ORACLE`, `SQLSERVER_NETV`, `SQLSERVER_AMEV` y la regla `tds_version=7.0` cuando
el prefijo contiene `"NETV"` (`sql_server.py:24`). Eso no es una librería
reutilizable: es la configuración de estos cuatro proyectos escrita en el código
compartido.

### 2.5 Logging (sección 6)

| Requisito | Estado | Evidencia |
|---|---|---|
| `log = logging.getLogger(__name__)` en cada módulo | NO | cero uso de `logging` en `db/*.py` |
| `NullHandler` en `__init__.py` | NO | verificado en runtime: `logging.getLogger("db").handlers == []` |
| Sin `basicConfig` ni `StreamHandler` en módulos | SÍ | grep sin coincidencias |
| `print()` solo para prompt al operador (MFA) | NO | `general.py:86` imprime el comentario de cada sentencia; `general.py:92` imprime el error antes de re-lanzar |
| `logs/` solo desarrollo y en `.gitignore` | NO | no existe logging ni `logs/` |

### 2.6 Excepciones y códigos de salida (sección 7)

| Requisito | Estado | Evidencia |
|---|---|---|
| `_excepciones.py` con `codigo_salida` como atributo de clase | NO | `MissingEnvironmentVariableError(RuntimeError)` en `_env.py:7`, sin código y con nombre en inglés |
| Tabla de códigos en el README (incluye 0 y 1) | NO | el README no la tiene |
| Entrada malformada como `ValueError` nativo | SÍ | `set_separador` lanza `ValueError` |

### 2.7 Tests (sección 8)

| Requisito | Estado | Evidencia |
|---|---|---|
| Tests en `tests/`, uno ejecutable por archivo con `main()` | NO | cero tests en la librería (es el único lugar del ecosistema donde se permiten) |
| Falla con mensaje claro si falta configuración | N/A | no hay tests |

### 2.8 Ejecutables (sección 9)

| Requisito | Estado | Evidencia |
|---|---|---|
| `ejecutables/build.bat` | NO | no existe |
| `ejecutables/abrir_vscode.bat` | NO | no existe |
| `ejecutables/tests/<test>.bat` (uno por test) | NO | no existe |
| `login.bat` solo si hay autenticación humana | N/A | `db` no requiere MFA |
| Sin `-- python`, sin `pause` en desatendidos | N/A | no hay `.bat` |

### 2.9 Versionado y control de versiones (sección 10)

| Requisito | Estado | Evidencia |
|---|---|---|
| Repositorio git con remoto GitHub | NO | *"not a git repository"*; `sharepoint` sí tiene `origin → github.com/SebaxFentex/sharepoint.git` |
| Versión `X.Y.Z` en `pyproject.toml` | SÍ | `0.1.1` |
| Versión coherente entre `pyproject`, `uv.lock` y `dist/` | NO | `0.1.1` / `0.1.0` / artefactos `db-0.1.0-*` |
| `uv build` sin warnings de `build_system.requires` | NO VERIFICADO | el backend no es `uv_build`, así que el chequeo de la norma no aplica todavía |
| Tag anotado + release al publicar | NO | sin repo no hay tags |
| Historial de rupturas de API en `AGENTS.md` | NO | no existe `AGENTS.md` |

### 2.10 README (sección 11)

| Requisito | Estado | Evidencia |
|---|---|---|
| 1. Qué hace **y qué no** | NO | describe qué hace; no delimita límites |
| 2. Cómo declararla editable | NO | propone `uv add ../ruta/...` y "instalación normal"; no muestra `[tool.uv.sources]` con `editable = true` |
| 3. Qué necesita el consumidor | PARCIAL | lista variables de entorno del modelo viejo; no dice requisitos, ni que no hay login |
| 4. Ejemplo mínimo copiable | SÍ | bloque `run_query` + `create_oracle_engine_from_env` |
| 5. API pública con firmas y excepciones | NO | no hay firmas ni tabla de excepciones |
| 6. Tabla de códigos de salida | NO | no existe |
| 7. Desarrollo (entorno, estructura, tests) | NO | no existe; en su lugar hay secciones "publicar más adelante" y "flujo recomendado de versionado" que ya no aplican |

### 2.11 Lineamientos generales (TIGO_GENERAL)

| Requisito | Estado | Evidencia |
|---|---|---|
| Español en identificadores (excepciones técnicas) | NO | `run_query`, `get_env`, `get_required_env`, `get_typed_env`, `create_*_engine_from_env`, `MissingEnvironmentVariableError`; `engine`/`sql`/`tds` sí se conservan por ser términos técnicos |
| `snake_case` | SÍ | — |
| Constantes `MAYUSCULAS_CON_GUIONES_BAJOS` | SÍ | `SEPARADOR` |
| Sin `ñ` en identificadores | SÍ | grep sin coincidencias |
| Sin symlinks/junctions y raíz `Tigo` sin `pyproject`/`uv.lock`/`.venv` | SÍ | `dir /AL /S` vacío; raíz limpia |
| Índice de librerías (sección 12) apunta a una ruta existente | SÍ | `db/README.md` existe |

---

## 3. Defectos de código verificados (no son de forma: rompen datos)

Verificados ejecutando el paquete real con Python 3.14.3 y los mismos pins de
`pyproject.toml` (venv desechable en el scratch, sin tocar la librería):

| # | Defecto | Prueba ejecutada | Resultado |
|---|---|---|---|
| B-1 | **Corrupción silenciosa de valores con backslash** en `_reemplazar_parametros` | `_reemplazar_parametros("select :ruta as x", {"ruta": r"C:\nuevo\archivo.txt"})` | devuelve `select 'C:\nuevo\x07rchivo.txt' as x`: `re.sub` interpreta `\n` y `\a` en el reemplazo. Cualquier ruta Windows o texto con `\` se guarda corrupta |
| B-2 | **El separador público queda congelado**: `db.SEPARADOR` es una copia hecha en el `import` | `set_separador("--OTRO")` y leer ambas referencias | `db.general.SEPARADOR` = `"--OTRO"`, `db.SEPARADOR` = `"--SEPARADOR DE CONSULTAS"` (sigue exportado en `__all__`) |
| B-3 | **Engines a nivel de módulo que fallan en silencio** | `import db` sin variables de entorno | `oracle_gdwh_ext_engine`, `sqlserver_netv_engine`, `sqlserver_amev_engine` quedan en `None` por `except Exception: pass`; el consumidor descubre que no hay conexión varias líneas después |
| B-4 | **Commit por sentencia**: un bloque de 5 updates deja 2 aplicados si el 3.º falla | lectura de `general.py:79-93` | `conn.execute(...)` + `conn.commit()` dentro del `for`: no hay atomicidad |
| B-5 | **Regla de negocio escondida en el nombre del prefijo** | `sql_server.py:24` | `if "NETV" in prefix: tds_version = "7.0"`: renombrar el prefijo cambia el driver |
| B-6 | **`oracledb.init_oracle_client` se ejecuta en cada creación de engine y otra vez al importar** | `oracle.py:31-32` y `oracle.py:47-51` | la inicialización es de proceso completo y no idempotente por diseño de `oracledb`; queda en el constructor en vez de ser una decisión explícita del consumidor |
| B-7 | **Trazas por `print`** en vez de `log` | `general.py:86,92` | un proceso desatendido no deja rastro y el mensaje se pierde |

Los siete desaparecen con el rediseño de la fase 3; no requieren parches
individuales.

---

## 4. Estado objetivo

```text
db/
├── src/db/
│   ├── __init__.py          # NullHandler + API pública (sin efectos al importar)
│   ├── _log.py              # configurar_log() para entrypoints/tests
│   ├── _excepciones.py      # ExcepcionConexion(2), ExcepcionEjecucionSql(3)
│   ├── conexion.py          # crear_engine_oracle / crear_engine_sqlserver (solo parámetros)
│   └── ejecucion.py         # SEPARADOR_CONSULTAS, ejecutar_sql()
├── tests/
│   ├── test_ejecutar_sql.py     # local, sqlite en memoria (sin credenciales)
│   ├── test_crear_engines.py    # local, inspecciona engine.url (sin conectar)
│   └── test_conexion.py         # e2e opcional, lee .env y falla con mensaje si falta
├── ejecutables/
│   ├── build.bat
│   ├── abrir_vscode.bat
│   └── tests/ (un .bat por test)
├── logs/                    # solo desarrollo, ignorado por git
├── .env / .env.example      # solo para el test e2e
├── .gitignore  .python-version  pyproject.toml  uv.lock
└── README.md  AGENTS.md
```

API objetivo (rompe la actual; ver decisión D1):

```python
from db import crear_engine_oracle, crear_engine_sqlserver, ejecutar_sql

engine = crear_engine_oracle(
    usuario=..., clave=..., host=..., servicio=...,
    puerto=1521, ruta_cliente_x64=None,   # None = thin mode
)
ejecutar_sql(sql, engine, parametros={"periodo": "2026-09"})
```

Tabla de migración viejo → nuevo:

| Actual | Nuevo | Nota |
|---|---|---|
| `create_oracle_engine_from_env(prefix)` | `crear_engine_oracle(usuario, clave, host, servicio, puerto=1521, ruta_cliente_x64=None)` | el consumidor lee su `.env` |
| `create_sqlserver_engine_from_env(prefix)` | `crear_engine_sqlserver(usuario, clave, host, base_datos, version_tds=None)` | `version_tds` explícito, no por nombre de prefijo |
| `create_sqlserver_netv_engine_from_env()` / `..._amev_...()` | se eliminan | eran dos constantes de negocio de Tigo |
| `sqlserver_netv_engine`, `sqlserver_amev_engine`, `oracle_gdwh_ext_engine` | se eliminan | efectos de import que fallan en silencio (B-3); `oracle_engine` ni siquiera existe y ya hay consumidores importándolo |
| `run_query(query, engine, parameters, separador)` | `ejecutar_sql(sql, engine, parametros=None, separador=SEPARADOR_CONSULTAS) -> list[CursorResult]` | binds reales de SQLAlchemy, una transacción, devuelve resultados |
| `set_separador()` / `get_separador()` / `db.SEPARADOR` | `separador=` por llamada y la constante `SEPARADOR_CONSULTAS` | sin estado global mutable |
| `db._env.*` | se elimina | la librería no lee entorno |
| `MissingEnvironmentVariableError` | se elimina | no hay variables de entorno que exigir; los errores de conexión propios salen como `ExcepcionConexion` |

---

## 5. Fases

Cada fase se cierra con su criterio de aceptación verificado; no se pasa a la
siguiente sin eso.

### F1 — Repositorio y reproducibilidad (P0)

```bash
cd "D:/Tigo/Proyectos/1. PROPIOS/1.5 - Librerias/db"
# 1) baseline antes de tocar nada (requiere D2 aprobada)
git init -b main
# crear .gitignore (bloque 6.1) ANTES del primer commit
git add -A && git commit -m "Estado inicial de la libreria db (0.1.1)"
git remote add origin https://github.com/SebaxFentex/db.git
git push -u origin main
# 2) limpiar artefactos y reconstruir entorno
rm -rf dist db/__pycache__
uv lock && uv sync
```

**Aceptación:** `git ls-remote --tags origin` responde (repo existe y tiene
remoto); `uv lock --check` termina sin error; existe `.venv/Scripts/python.exe`;
`git status --short` vacío.

### F2 — Layout de paquete y backend (P0)

```bash
mkdir -p src
git mv db src/db
# editar pyproject.toml (bloque 6.2) y .python-version -> 3.14
uv lock && uv sync
uv build
```

**Aceptación:** `uv build` sin ninguna advertencia de `build_system.requires`;
`dist/db-0.2.0-py3-none-any.whl` contiene `db/__init__.py`;
`.venv/Scripts/python.exe -c "import db; print(db.__file__)"` imprime una ruta
dentro de `src\db`; `uv run python -c "import db"` desde la raíz no depende de
tener la raíz en el `PATH`.

### F3 — Rediseño de API (rompe consumidores)

Archivos: `src/db/conexion.py`, `src/db/ejecucion.py`, `src/db/_excepciones.py`,
`src/db/_log.py`, `src/db/__init__.py`. Se elimina `src/db/_env.py`,
`src/db/general.py`, `src/db/oracle.py`, `src/db/sql_server.py`.

**Aceptación:**
- `grep -rn "getenv\|os.environ\|load_dotenv\|SEPARADOR\b" src/` sin coincidencias.
- `grep -rn "print(\|basicConfig\|init_oracle_client" src/` sin coincidencias.
- `import db` sin ninguna variable de entorno definida y sin crear engines.
- El valor `r"C:\nuevo\archivo.txt"` llega intacto a la base (regresión de B-1).
- Un bloque de 3 sentencias donde la 3.ª falla no deja las 2 primeras aplicadas.

### F4 — Tests y ejecutables

**Aceptación:** los tres tests corren con `uv run` y devuelven 0; el test e2e
devuelve 2 con mensaje claro cuando falta `.env`; `cmd /c "ejecutables\build.bat"`
llega al `pause` final listando `dist\`; cada `.bat` de test propaga el código.

### F5 — Documentación

`README.md` reescrito en las 7 secciones obligatorias (uso primero, desarrollo
después) y `AGENTS.md` nuevo con arquitectura, reglas inviolables, verificación e
historial de rupturas.

**Aceptación:** `grep -rn "run_query\|_from_env\|sqlserver_netv_engine\|db.SEPARADOR" README.md AGENTS.md` sin coincidencias; el README tiene tabla de
códigos con 0/1/2/3 y el snippet `editable = true` con los cuatro `../`.

### F6 — Publicación

```bash
# version 0.2.0 en pyproject.toml
uv lock && uv build
git add -A && git commit -m "v0.2.0: libreria db como paquete uv_build, API por parametros y tests"
git tag -a v0.2.0 -m "v0.2.0: paquete uv_build, API sin entorno, tests y ejecutables"
git push origin main --follow-tags
git ls-remote --tags origin
```

**Aceptación:** el tag aparece en el remoto (no solo local) y la versión del
`pyproject.toml` en el commit tagueado es `0.2.0`.

---

## 6. Bloques listos para pegar

### 6.1 `.gitignore`

```gitignore
# Python
__pycache__/
*.py[oc]
.venv/
*.egg-info/
dist/

# Configuracion local
.env

# Salidas de tests
tests/archivos/descarga/

# Logs de desarrollo (los crea configurar_log al correr tests)
logs/
```

### 6.2 `pyproject.toml`

(El bloque muestra el estado final: la versión se sube a `0.2.0` en F6; el resto
aplica desde F2.)

```toml
[project]
name = "db"
version = "0.2.0"
description = "Utilidades para crear engines de SQLAlchemy y ejecutar SQL en Oracle y SQL Server"
readme = "README.md"
authors = [
    { name = "Sebastián Fuentes", email = "sebastianfuentesab@gmail.com" }
]
requires-python = ">=3.14"
dependencies = [
    "oracledb==3.4.1",
    "pymssql==2.3.10",
    "sqlalchemy==2.0.45",
]

[dependency-groups]
dev = [
    "ipykernel==7.1.0",
]

[build-system]
requires = ["uv_build>=0.13.0,<1.0"]
build-backend = "uv_build"
```

### 6.3 `.env.example` (solo para el test e2e)

```dotenv
# Configuracion LOCAL para los entrypoints de este repo (tests).
# Copiar a `.env` (ignorado por git) y ajustar. La libreria NO lee este
# archivo: solo recibe parametros explicitos.
#
# Uso: uv run --env-file .env python tests/test_conexion.py

# Oracle de prueba (requerido por test_conexion.py).
ORACLE_USUARIO=usuario
ORACLE_CLAVE=cambiar
ORACLE_HOST=host:puerto/servicio

# SQL Server de prueba (opcional; el test lo omite si no esta definido).
SQLSERVER_USUARIO=usuario
SQLSERVER_CLAVE=cambiar
SQLSERVER_HOST=host
SQLSERVER_BD=base_de_datos
```

### 6.4 `ejecutables/build.bat`

```bat
@echo off
cd /d "%~dp0.."
echo Construyendo paquete...
uv build
if errorlevel 1 (
    echo ERROR: la construccion fallo.
    pause
    exit /b 1
)
echo.
echo Artefactos generados en dist\:
dir /b dist
pause
```

### 6.5 `ejecutables/abrir_vscode.bat`

```bat
@echo off
code "%~dp0.."
```

### 6.6 `ejecutables/tests/test_ejecutar_sql.bat` (patrón; uno por test)

```bat
@echo off
cd /d "%~dp0..\.."
uv run python tests/test_ejecutar_sql.py
set EXIT_CODE=%ERRORLEVEL%
echo.
echo Codigo de salida: %EXIT_CODE%
pause
exit /b %EXIT_CODE%
```

(Este test no necesita `.env` porque usa sqlite en memoria. Solo
`test_conexion.bat` lleva `uv run --env-file .env`.)

---

## 7. Decisiones abiertas

| # | Decisión | Opciones | Recomendación |
|---|---|---|---|
| D1 | Alcance de la ruptura de API | (a) rediseño completo: fuera `*_from_env`, fuera engines de módulo, fuera separador global, nombres en español. (b) mantener los nombres viejos como envoltorios que además lean entorno | (a). El usuario no quiere compatibilidad heredada y los envoltorios obligarían a la librería a seguir leyendo entorno, que es justo lo que la sección 5 prohíbe. Costo: 20 archivos de 4 proyectos B2B (2.6, 2.8, 2.9, 2.10) que se migran después, proyecto por proyecto |
| D2 | Repositorio git y remoto | (a) `git init` + remoto `github.com/SebaxFentex/db` + push del baseline. (b) repo solo local, sin remoto | (a): la sección 10 exige origen en GitHub y sin repo no hay tag ni release. Crear el repo remoto es acción externa: requiere confirmación |
| D3 | Número de versión del cambio | (a) `0.2.0` (menor: ruptura migrable con aviso). (b) `1.0.0` (mayor: rediseño que obliga a reescribir el consumo) | (a) `0.2.0`. La norma reserva el salto a `1.0.0` para la primera versión estable; conviene estrenarla cuando los consumidores ya estén migrados y verificados |
| D4 | Cobertura de tests | (a) solo locales con sqlite (sin credenciales, siempre corren). (b) locales + e2e contra Oracle y SQL Server reales | (b): los locales prueban la lógica (separador, binds, atomicidad, excepciones); el e2e es el único que valida que `pymssql`/`oracledb` conectan de verdad. El e2e queda opcional y falla con mensaje si falta `.env` |
| D5 | Nombres de módulos y funciones | (a) `conexion.py` + `ejecucion.py`, `crear_engine_*`, `ejecutar_sql`. (b) `sql.py` + `consultas.py`, `ejecutar_consulta` | (a): `engine` es término de SQLAlchemy y la sección 6 del criterio de conceptos técnicos lo ampara; `ejecucion.py` describe lo que hace |
| D6 | `tds_version` de NETV | (a) parámetro explícito `version_tds="7.0"` en cada consumidor de NETV. (b) quitar `7.0` y usar el default de pymssql | (a) primero: conserva el comportamiento actual verificado. Requiere que el usuario confirme si NETV necesita `7.0` de verdad o si era un parche histórico |

---

## 8. Checklist de aceptación

- [ ] `uv lock --check` sin error y `.venv` propio creado por `uv sync`
- [ ] `uv build` sin advertencias; wheel generado con `db/` adentro
- [ ] `import db` sin variables de entorno, sin crear engines y sin `print`
- [ ] `grep` de `getenv`, `os.environ`, `load_dotenv`, `basicConfig`, `print(` en `src/`: vacío
- [ ] `NullHandler` presente; `logging.getLogger("db").handlers` no vacío
- [ ] `_excepciones.py` con `codigo_salida` 2 y 3, documentados en el README
- [ ] Los tres tests corren con `uv run` y devuelven 0; regresión de backslash cubierta
- [ ] `ejecutables/` con `build.bat`, `abrir_vscode.bat` y un `.bat` por test
- [ ] `.gitignore` ignora `.venv/`, `__pycache__/`, `dist/`, `.env`, `logs/`
- [ ] `README.md` con las 7 secciones en orden; `AGENTS.md` con historial de rupturas
- [ ] Repo git con remoto GitHub, commit y tag `v0.2.0` verificados con `git ls-remote`
- [ ] Cero menciones a `run_query`, `_from_env`, `sqlserver_netv_engine` o `db.SEPARADOR` en código y docs

---

## 9. Fuera de alcance

Se detectó y **no** se toca en este plan:

1. **Los dos consumidores** (`python_portaciones`, `python_reportes_interbd`)
   declaran `db = { path = "../../../../Python/librerias/db", editable = true }`,
   ruta inexistente. Se corrige a
   `../../../../Proyectos/1. PROPIOS/1.5 - Librerias/db` en la migración de cada
   proyecto, no aquí.
2. **Consumidores que importan `oracle_engine`** (`from db.oracle import
   oracle_engine` en 7 notebooks y 2 `main.py`): ese nombre no existe en la
   librería actual, así que ya están rotos hoy. Se migran a `crear_engine_oracle`
   con parámetros.
3. **`D:/Tigo/Tareas/`** no se inspecciona ni se modifica (producción, es de
   `tigo-operador`). Si algún proceso productivo importa `db`, la migración de
   ese consumidor la decide el dueño de la tarea.
4. **Librería `excel`** (misma categoría, `1.5 - Librerias/excel`): está aún más
   lejos de la norma (paquete en la raíz, `hatchling`, sin `.venv`, sin
   `uv.lock`, sin `tests/`, `abrir vscode.bat` suelto en la raíz, `requires-python >=3.13`).
   Merece su propia auditoría con este mismo procedimiento.
5. **`LICENSE`**: `sharepoint` lo tiene y la norma no lo exige; no se agrega sin
   decisión del usuario.
6. **`changelog`/release notes en GitHub**: se crean en el release de F6, no
   antes.
