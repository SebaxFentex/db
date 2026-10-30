# AGENTS.md — db

Guia para agentes (y humanos) que trabajan en este repo. Cada regla con su
"porque" viene de un defecto real; no relajarla sin evidencia nueva.

## 1. Proyecto en 30 segundos

Libreria interna PAQUETE (`uv_build`, layout `src/`) que construye engines de
SQLAlchemy para Oracle y SQL Server y ejecuta bloques de SQL en una sola
transaccion. Se consume en modo editable desde los `pyproject.toml` de los
proyectos de `D:\Tigo\Proyectos`; no se opera con el Programador de tareas y no
pide credenciales a ningun humano.

Stack: Python 3.14, `uv`, SQLAlchemy 2.1, `oracledb` 26 (thin por defecto),
`pymssql` 2.4.

```text
src/db/
  __init__.py        NullHandler + API publica (sin re-exports de modulos internos)
  _log.py            configurar_log() + purgar_logs() — solo para entrypoints
  _excepciones.py    ExcepcionDb (1), ExcepcionConexion (2), ExcepcionEjecucionSql (3)
  conexion.py        crear_engine_oracle / crear_engine_sqlserver / inicializar_cliente_oracle
  ejecucion.py       SEPARADOR_CONSULTAS, ResultadoSql, ejecutar_sql
ejecutables/
  build.bat          uv build y lista dist/
  abrir_vscode.bat   abre la raiz de la libreria
  tests/             un .bat por test (mismo nombre que el .py)
tests/
  test_ejecutar_sql.py   local, sqlite en memoria (sin credenciales)
  test_crear_engines.py  local, inspecciona la URL del engine (sin conectar)
  test_conexion.py       e2e contra Oracle/SQL Server, lee .env
logs/                    logs de desarrollo (ignorado por git)
```

## 2. Arquitectura y API

- **La libreria no lee entorno.** `import db` no exige ninguna variable y no
  abre conexiones. Todo entra por parametro: el `.env` es del consumidor.
- `crear_engine_oracle(usuario, clave, host, servicio, puerto=1521, query=None)`
  y `crear_engine_sqlserver(usuario, clave, host, base_datos, puerto=None, query=None)`:
  construyen la URL y devuelven un `Engine` con `pool_pre_ping=True` y
  `pool_recycle=1800`. No conectan.
- `query` es la valvula para opciones del driver. **Las bases antiguas que solo
  hablan TDS 7.0 se conectan pasando `query={"tds_version": "7.0"}` desde el
  proyecto consumidor**: la libreria no decide eso por el nombre del prefijo.
- `ejecutar_sql(sql, engine, parametros=None, separador=SEPARADOR_CONSULTAS)`
  devuelve `list[ResultadoSql]`. Abre la conexion fuera de la transaccion para
  poder distinguir el error de conexion (2) del error de SQL (3).
- `inicializar_cliente_oracle(ruta_cliente)` es el unico punto que toca estado
  del proceso (modo thick), es idempotente por ruta y solo se llama si el
  consumidor lo pide.
- Orden de metodos y funciones: publicas primero, privadas (`_nombre`) despues.

## 3. Reglas inviolables

1. **Cero lecturas de entorno en la libreria.** `conexion.py` y `ejecucion.py`
   no importan `os`; la unica excepcion es `DB_NIVEL_LOG` dentro de `_log.py`,
   que es un entrypoint de desarrollo. Un valor que cambia por maquina se pasa
   como parametro.
2. **Parametros ligados, nunca interpolacion.** Los valores viajan por
   `:nombre` a SQLAlchemy. Interpolar con `re.sub` corrompe datos (un `\n` de
   una ruta Windows se convierte en salto de linea) y abre inyeccion de SQL.
   Prohibido volver a construir SQL con f-strings o `%`.
3. **Una transaccion por llamada.** Nada de `commit()` por sentencia: un bloque
   de cinco updates dejaba dos aplicados si el tercero fallaba.
4. **La libreria emite, el entrypoint configura.** `logging.getLogger(__name__)`
   en cada modulo y `NullHandler` en el paquete; `configurar_log()` solo se llama
   desde `tests/*`. Prohibido `basicConfig()` y prohibido que un modulo que emite
   agregue manejadores: el unico que agrega es `_log.configurar_log()`, y lo hace
   sobre el logger "db", nunca sobre el raiz del consumidor.
5. **Sin `print()`.** El unico destino de las trazas es `log`; un proceso
   desatendido con `print` no deja rastro. El encabezado `--` de cada sentencia
   se registra en INFO (rastro auditable) y el detalle en DEBUG.
6. **Nada de objetos globales mutables.** El separador es un parametro con
   default; `set_separador()` y el `SEPARADOR` re-exportado se eliminaron porque
   el `__init__` se quedaba con la copia hecha al importar y mentia.
7. **Sin efectos al importar.** Prohibido crear engines a nivel de modulo y
   tragarte la excepcion con `except Exception: engine = None`: el consumidor
   descubria el problema mucho despues.
8. **Errores clasificados por donde ocurren.** Conexion (2) es lo que falla al
   abrir o al perder la conexion, incluido el `OSError`/`socket.gaierror` que
   `oracledb` thin lanza antes de que SQLAlchemy lo envuelva. SQL (3) es lo que
   rechaza la base. La entrada malformada se deja nativa: `TypeError` si el
   valor no es texto (`None`, un numero) y `ValueError` si es texto pero llega
   vacio o solo con espacios. Nunca se envuelve en `ExcepcionDb`.
9. **`.bat` de proceso en `ejecutables/` invocando `uv run`.** Un `.bat` por
   test en `ejecutables/tests/`, con `pause` para leer el resultado y
   propagacion del codigo de salida. `abrir_vscode.bat` es utilitario: no lleva
   `uv run`.
10. **Nada especulativo.** Sin abstracciones de un solo uso ni parametros de
    "por si acaso". Lo muerto se borra: queda en git si se necesita.

## 4. Logging, codigos de salida y `.env`

- `configurar_log(nivel=None, prefijo="db-", conservar=30)` configura el logger
  "db" (no el raiz) con archivo y consola en `logs/` (utf-8), purga los antiguos
  y es idempotente: la segunda llamada no agrega manejadores. Nivel por
  parametro > `DB_NIVEL_LOG` > INFO; un valor invalido cae a INFO. Devuelve el
  `Logger` configurado.
- Codigos: `0` correcto · `1` fallo generico · `2` conexion · `3` SQL. El
  consumidor hace `sys.exit(exc.codigo_salida)`.
- `.env` local (ignorado por git) solo lo usa `tests/test_conexion.py`. Se
  versiona `.env.example` con placeholders: `ORACLE_USUARIO`, `ORACLE_CLAVE`,
  `ORACLE_HOST`, `ORACLE_SERVICIO` (y opcionales `ORACLE_PUERTO`,
  `ORACLE_RUTA_CLIENTE`), `SQLSERVER_USUARIO`, `SQLSERVER_CLAVE`,
  `SQLSERVER_HOST`, `SQLSERVER_BD` (y opcionales `SQLSERVER_PUERTO`,
  `SQLSERVER_TDS`), `DB_NIVEL_LOG`.
- Nunca loguear credenciales: para describir un engine se usa
  `engine.url.render_as_string(hide_password=True)`.

## 5. Verificacion antes de dar por hecho

1. `uv run python -m compileall -q src/db`.
2. `import db` con el entorno vacio: sin error, `handlers` con el `NullHandler`
   y ningun engine creado.
3. `uv run python tests/test_ejecutar_sql.py` y `uv run python tests/test_crear_engines.py`
   en 0. El e2e (`tests/test_conexion.py`) necesita credenciales reales: si no
   hay `.env`, se reporta como no verificado en vez de darlo por bueno.
4. `uv build` sin advertencias de `build_system.requires`; el wheel debe traer
   `db/__init__.py`.
5. Greps de guardia: cero `getenv`/`os.environ` fuera de `_log.py`, cero
   `print(`, cero `basicConfig`, cero `set_separador`, cero `_from_env`, cero
   `load_dotenv`, cero `cwd(`.
6. Los `.bat` se prueban ejecutandolos: `cmd.exe /c ejecutables\build.bat` debe
   llegar al `pause` final listando `dist\`.

## 6. Historial de rupturas

- **v0.2.0 (2026-10-28)**: la libreria deja de leer entorno y pasa a ser un
  paquete `uv_build` con layout `src/`. Mapeo viejo -> nuevo:
  `create_oracle_engine_from_env(prefix)` -> `crear_engine_oracle(usuario, clave,
  host, servicio, puerto=1521, query=None)`; `create_sqlserver_engine_from_env(prefix)`
  -> `crear_engine_sqlserver(usuario, clave, host, base_datos, puerto=None,
  query=None)`; `create_sqlserver_netv_engine_from_env()` y
  `create_sqlserver_amev_engine_from_env()` se eliminan (eran dos constantes de
  negocio de Tigo dentro de la libreria: el consumidor arma su engine con sus
  propios valores); `sqlserver_netv_engine`, `sqlserver_amev_engine` y
  `oracle_gdwh_ext_engine` se eliminan (efectos de import que fallaban en
  silencio); `run_query(query, engine, parameters, separador)` -> `ejecutar_sql(sql,
  engine, parametros=None, separador=SEPARADOR_CONSULTAS)` y ahora devuelve
  `list[ResultadoSql]`; `set_separador()`/`get_separador()`/`db.SEPARADOR` ->
  parametro `separador` y constante `SEPARADOR_CONSULTAS`; `db._env.*` y
  `MissingEnvironmentVariableError` se eliminan; `DB_SEPARADOR` deja de existir.
  El `tds_version=7.0` que la libreria aplicaba sola cuando el prefijo contenia
  `"NETV"` pasa a ser `query={"tds_version": "7.0"}` en el consumidor. Los
  proyectos que la consumen deben migrar: `python_portaciones`,
  `python_tabla_calendario`, `python_simplificacion_planes` y
  `python_reportes_interbd`.
- **v0.2.1 (2026-10-28)**: `_log.py` se alinea con el de `sharepoint`
  (`carpeta_logs()`, constantes `PREFIJO_LOG_PREDETERMINADO`,
  `NIVEL_LOG_PREDETERMINADO` y `MAX_LOGS_PREDETERMINADO`, configuracion del
  logger "db" en vez del raiz, idempotente, nivel por parametro > `DB_NIVEL_LOG`
  > INFO, purga por nombre y devuelve el `Logger`). Dependencias al dia:
  `oracledb` 3.4.1 -> 26.1.0, `pymssql` 2.3.10 -> 2.4.6, `sqlalchemy` 2.0.45 ->
  2.1.6, `ipykernel` 7.1.0 -> 7.4.0. Sin cambios de API.
- **v0.2.2 (2026-10-28)**: renombre de helpers internos para que el nombre diga
  lo que hacen. En `conexion.py`, `_exigir(valor, nombre)` pasa a
  `_texto_obligatorio(valor, nombre)`. En `tests/test_conexion.py`,
  `_exigir(nombre)` pasa a `_leer_variable_obligatoria(nombre)` y
  `_opcional(nombre)` a `_leer_variable_opcional(nombre)`: el mismo nombre
  cubria dos contratos distintos (validar un valor vs leer una variable de
  entorno). Sin cambios de API ni de comportamiento.
- **v0.3.0 (2026-10-30)**: el contrato de errores separa tipo de contenido.
  `_verificar_parametro_obligatorio` recibe `valor: object` (es un validador: no
  puede dar por hecho que ya recibe texto) y lanza `TypeError` cuando el valor no
  es texto (`None`, un numero) y `ValueError` cuando es texto pero llega vacio o
  solo con espacios. Antes los dos casos salian como `ValueError`. Un consumidor
  que atrapaba `ValueError` para el caso de la variable ausente
  (`os.environ.get` devuelve `None`) debe atrapar tambien `TypeError`.
  `tests/test_crear_engines.py` cubre los dos caminos; ademas el test estrecha
  `engine.pool` a `QueuePool` antes de `checkedout()`, porque ese metodo no
  existe en la clase base `Pool`.
