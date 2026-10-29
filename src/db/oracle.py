from __future__ import annotations

import oracledb
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, URL

from ._env import get_env, get_required_env, get_typed_env


def create_oracle_engine_from_env(prefix: str = "ORACLE") -> Engine:
    """
    Crea un engine de Oracle leyendo variables de entorno.

    Variables requeridas:
    - {prefix}_USER
    - {prefix}_PASSWORD
    - {prefix}_HOST
    - {prefix}_SERVICE_NAME

    Variables opcionales:
    - {prefix}_PORT (default: 1521)
    - {prefix}_X64_PATH (si existe, inicializa Oracle Client)
    """
    user = get_required_env(f"{prefix}_USER")
    password = get_required_env(f"{prefix}_PASSWORD")
    host = get_required_env(f"{prefix}_HOST")
    service_name = get_required_env(f"{prefix}_SERVICE_NAME")
    port = get_typed_env(f"{prefix}_PORT", int, 1521)
    x64_path = get_env(f"{prefix}_X64_PATH")

    if x64_path:
        oracledb.init_oracle_client(lib_dir=x64_path)

    oracle_url = URL.create(
        drivername="oracle+oracledb",
        username=user,
        password=password,
        host=host,
        port=port,
        database=None,
        query={"service_name": service_name},
    )

    return create_engine(oracle_url)


# Conveniencia para mantener compatibilidad con el nombre historico.
try:
    oracle_gdwh_ext_engine = create_oracle_engine_from_env("ORACLE")
except Exception:
    oracle_gdwh_ext_engine = None
