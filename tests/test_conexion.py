"""Test e2e opcional contra Oracle y SQL Server reales.

Lee la configuracion del `.env` local (ver `.env.example`). Si no hay ninguna
base configurada falla con mensaje, en lugar de inventar valores por defecto.
Se puede limitar a un motor definiendo solo su bloque de variables.

Uso: uv run --env-file .env python tests/test_conexion.py
"""

from __future__ import annotations

import logging
import os

from sqlalchemy import Engine

from db import (
    ExcepcionConexion,
    ExcepcionEjecucionSql,
    crear_engine_oracle,
    crear_engine_sqlserver,
    ejecutar_sql,
    inicializar_cliente_oracle,
)
from db._log import configurar_log

log = logging.getLogger("db.tests")


def _exigir(nombre: str) -> str:
    """Devuelve la variable obligatoria o corta con mensaje (sin defaults inventados)."""
    valor = (os.environ.get(nombre) or "").strip()
    if not valor:
        raise SystemExit(
            f"Falta {nombre} en el .env local (ver .env.example). "
            "Sin esa variable no se puede probar la conexion."
        )
    return valor


def _opcional(nombre: str) -> str | None:
    valor = (os.environ.get(nombre) or "").strip()
    return valor or None


def _probar_oracle() -> None:
    usuario = _exigir("ORACLE_USUARIO")
    clave = _exigir("ORACLE_CLAVE")
    host = _exigir("ORACLE_HOST")
    servicio = _exigir("ORACLE_SERVICIO")
    puerto = _opcional("ORACLE_PUERTO")
    ruta_cliente = _opcional("ORACLE_RUTA_CLIENTE")

    if ruta_cliente:
        inicializar_cliente_oracle(ruta_cliente)

    engine = crear_engine_oracle(
        usuario=usuario,
        clave=clave,
        host=host,
        servicio=servicio,
        puerto=int(puerto) if puerto else 1521,
    )
    _consultar(engine, "select 1 as uno from dual", "Oracle")


def _probar_sqlserver() -> None:
    usuario = _exigir("SQLSERVER_USUARIO")
    clave = _exigir("SQLSERVER_CLAVE")
    host = _exigir("SQLSERVER_HOST")
    base_datos = _exigir("SQLSERVER_BD")
    puerto = _opcional("SQLSERVER_PUERTO")
    tds = _opcional("SQLSERVER_TDS")

    engine = crear_engine_sqlserver(
        usuario=usuario,
        clave=clave,
        host=host,
        base_datos=base_datos,
        puerto=int(puerto) if puerto else None,
        query={"tds_version": tds} if tds else None,
    )
    _consultar(engine, "select 1 as uno", "SQL Server")


def _consultar(engine: Engine, sql: str, motor: str) -> None:
    try:
        resultados = ejecutar_sql(sql, engine)
    except ExcepcionConexion as exc:
        log.error("Fallo la conexion a %s: %s", motor, exc)
        raise SystemExit(exc.codigo_salida) from exc
    except ExcepcionEjecucionSql as exc:
        log.error("Fallo la consulta en %s: %s", motor, exc)
        raise SystemExit(exc.codigo_salida) from exc

    filas = resultados[0].filas
    assert filas and filas[0][0] == 1, f"{motor} devolvio {filas}"
    log.info("OK conexion y consulta en %s: %s", motor, filas)


def main() -> None:
    configurar_log()
    log.info("Test de conexion e2e")

    motores = []
    if os.environ.get("ORACLE_USUARIO"):
        motores.append(("Oracle", _probar_oracle))
    if os.environ.get("SQLSERVER_USUARIO"):
        motores.append(("SQL Server", _probar_sqlserver))
    if not motores:
        raise SystemExit(
            "No hay ninguna base configurada: define ORACLE_USUARIO... o "
            "SQLSERVER_USUARIO... en el .env local (ver .env.example)."
        )

    for nombre, prueba in motores:
        log.info("Probando %s", nombre)
        prueba()

    log.info("OK test_conexion completo (%s)", ", ".join(nombre for nombre, _ in motores))


if __name__ == "__main__":
    main()
