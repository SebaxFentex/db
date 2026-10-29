from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, URL

from ._env import get_required_env


def create_sqlserver_engine_from_env(prefix: str) -> Engine:
    """
    Crea un engine SQL Server leyendo variables de entorno.

    Variables requeridas:
    - {prefix}_USER
    - {prefix}_PASSWORD
    - {prefix}_HOST
    - {prefix}_DB
    """
    user = get_required_env(f"{prefix}_USER")
    password = get_required_env(f"{prefix}_PASSWORD")
    host = get_required_env(f"{prefix}_HOST")
    database = get_required_env(f"{prefix}_DB")

    query = {"tds_version": "7.0"} if "NETV" in prefix else {}

    url = URL.create(
        drivername="mssql+pymssql",
        username=user,
        password=password,
        host=host,
        database=database,
        query=query,
    )

    return create_engine(url)


def create_sqlserver_netv_engine_from_env() -> Engine:
    return create_sqlserver_engine_from_env("SQLSERVER_NETV")


def create_sqlserver_amev_engine_from_env() -> Engine:
    return create_sqlserver_engine_from_env("SQLSERVER_AMEV")


# Compatibilidad con variables historicas.
try:
    sqlserver_netv_engine = create_sqlserver_netv_engine_from_env()
except Exception:
    sqlserver_netv_engine = None

try:
    sqlserver_amev_engine = create_sqlserver_amev_engine_from_env()
except Exception:
    sqlserver_amev_engine = None
