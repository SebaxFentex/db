from __future__ import annotations

import re

from sqlalchemy import Engine, text
from sqlalchemy.exc import DatabaseError

from ._env import get_env

SEPARADOR = get_env("DB_SEPARADOR", "--SEPARADOR DE CONSULTAS")


def set_separador(value: str) -> None:
    global SEPARADOR
    if not value or not value.strip():
        raise ValueError("El separador no puede estar vacio")
    SEPARADOR = value


def get_separador() -> str:
    return SEPARADOR


def _reemplazar_parametros(query: str, parameters: dict | None) -> str:
    """
    Reemplaza los parametros en el query antes de ejecutar.
    Los parametros se identifican con :nombre_parametro.
    Si el valor es texto, se le agregan comillas simples (escapando comillas internas).
    """
    if not parameters:
        return query

    resultado = query
    for nombre, valor in parameters.items():
        patron = rf":({nombre})(?=\s|$|,|\)|\]|;|'|\")"

        if valor is None:
            valor_reemplazo = "NULL"
        elif isinstance(valor, str):
            valor_escapado = valor.replace("'", "''")
            valor_reemplazo = f"'{valor_escapado}'"
        elif isinstance(valor, bool):
            valor_reemplazo = "1" if valor else "0"
        elif isinstance(valor, (int, float)):
            valor_reemplazo = str(valor)
        else:
            valor_escapado = str(valor).replace("'", "''")
            valor_reemplazo = f"'{valor_escapado}'"

        resultado = re.sub(patron, valor_reemplazo, resultado)

    return resultado


def run_query(
    query: str,
    engine: Engine,
    parameters: dict | None = None,
    separador: str | None = None,
) -> None:
    """
    Ejecuta uno o varios queries SQL usando un engine de SQLAlchemy.

    Args:
        query: SQL a ejecutar.
        engine: Engine de SQLAlchemy.
        parameters: Parametros a reemplazar en el SQL con formato :nombre.
        separador: Separador opcional para ejecutar multiples consultas.
                   Si no se envia, usa la variable global SEPARADOR.
    """
    query_procesado = _reemplazar_parametros(query, parameters)
    separador_efectivo = separador if separador is not None else SEPARADOR

    if separador_efectivo in query_procesado:
        consultas = [q.strip() for q in query_procesado.split(separador_efectivo) if q.strip()]
    else:
        consultas = [query_procesado.strip()]

    with engine.connect() as conn:
        for consulta in consultas:
            if not consulta:
                continue

            lineas = consulta.strip().split("\n")
            if lineas and lineas[0].strip().startswith("--"):
                print(lineas[0].strip())

            try:
                conn.execute(text(consulta))
                conn.commit()
            except DatabaseError as e:
                print(f"Error ejecutando consulta: {e}")
                raise
