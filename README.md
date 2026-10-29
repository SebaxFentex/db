# db

Libreria personal para utilidades de base de datos con SQLAlchemy:

- Oracle (driver `oracledb`)
- SQL Server (driver `pymssql`)
- Ejecucion de SQL con separador configurable para multiples consultas

## Variables de entorno

Esta libreria ya no depende de `env.py`.

Oracle (`ORACLE_*`):

- `ORACLE_USER` (requerida)
- `ORACLE_PASSWORD` (requerida)
- `ORACLE_HOST` (requerida)
- `ORACLE_SERVICE_NAME` (requerida)
- `ORACLE_PORT` (opcional, default `1521`)
- `ORACLE_X64_PATH` (opcional, para `oracledb.init_oracle_client`)

SQL Server NETV (`SQLSERVER_NETV_*`):

- `SQLSERVER_NETV_USER`
- `SQLSERVER_NETV_PASSWORD`
- `SQLSERVER_NETV_HOST`
- `SQLSERVER_NETV_DB`

SQL Server AMEV (`SQLSERVER_AMEV_*`):

- `SQLSERVER_AMEV_USER`
- `SQLSERVER_AMEV_PASSWORD`
- `SQLSERVER_AMEV_HOST`
- `SQLSERVER_AMEV_DB`

Separador de consultas:

- `DB_SEPARADOR` (opcional, default `--SEPARADOR DE CONSULTAS`)

## Uso rapido

```python
from db.general import run_query, set_separador
from db.oracle import create_oracle_engine_from_env

engine = create_oracle_engine_from_env()

# Opcional: cambiar separador global
set_separador("--MI_SEPARADOR")

sql = """
-- Insercion
insert into tabla_a(campo) values('x')
--MI_SEPARADOR
-- Actualizacion
update tabla_a set campo='y' where campo='x'
"""

run_query(sql, engine)
```

Tambien puedes sobrescribir el separador solo en una llamada:

```python
run_query(sql, engine, separador="--OTRO_SEPARADOR")
```

## Instalar esta libreria en otro proyecto (uso personal)

Si quieres trabajar por versiones (sin editable), usa instalacion normal:

```bash
uv add ../ruta/a/esta/libreria
```

Cuando cambies esta libreria y quieras que otro proyecto reciba cambios:

1. Sube la version en pyproject.toml (por ejemplo, 0.1.0 -> 0.1.1).
2. En el proyecto consumidor, actualiza dependencias:

```bash
uv lock
uv sync
```

## Flujo recomendado de versionado

- Usa SemVer simple:
	- PATCH (`0.1.0` -> `0.1.1`) para fixes internos y cambios chicos.
	- MINOR (`0.1.1` -> `0.2.0`) para nuevas funciones compatibles.
	- MAJOR (`0.x` -> `1.0.0`) si rompes compatibilidad.

Checklist rapido por version:

1. Cambia `version` en `pyproject.toml`.
2. (Opcional pero recomendado) crea un tag git: `vX.Y.Z`.
3. En cada proyecto consumidor, ejecuta `uv lock` y `uv sync`.

## Publicar mas adelante (opcional)

Si despues quieres compartirla:

1. Sube el repo a GitHub.
2. Instalala directo desde git en tus proyectos:

```bash
uv add git+https://github.com/tu-usuario/db.git
```

Si quieres fijar una version exacta por tag:

```bash
uv add git+https://github.com/tu-usuario/db.git@v0.1.0
```

Para uso solo tuyo, el flujo local por path editable suele ser lo mas comodo.
