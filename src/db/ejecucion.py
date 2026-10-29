"""Ejecucion de una o varias sentencias SQL sobre un engine de SQLAlchemy.

Los valores viajan como parametros ligados (``:nombre``): nunca se interpolan
en el texto del SQL, asi que una ruta con backslash o una comilla llegan
intactas y no hay forma de inyectar SQL por el valor de un parametro.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from sqlalchemy import Engine, text
from sqlalchemy.exc import InterfaceError, SQLAlchemyError

from ._excepciones import ExcepcionConexion, ExcepcionEjecucionSql

log = logging.getLogger(__name__)

SEPARADOR_CONSULTAS = "--SEPARADOR DE CONSULTAS"

# Marcadores de parametro tipo :nombre (sin confundirlos con los :: de un cast).
_PATRON_MARCADOR = re.compile(r"(?<!:):([A-Za-z_][A-Za-z0-9_]*)")


@dataclass(frozen=True)
class ResultadoSql:
    """Resultado de una sentencia ejecutada.

    Attributes:
        sentencia: el texto de la sentencia que se ejecuto.
        filas: filas devueltas, como tuplas; vacio si no devuelve filas.
        filas_afectadas: filas insertadas/actualizadas/borradas, o ``None`` si
            la sentencia devuelve filas o el driver no informa el dato.
    """

    sentencia: str
    filas: list[tuple] = field(default_factory=list)
    filas_afectadas: int | None = None


def ejecutar_sql(
    sql: str,
    engine: Engine,
    parametros: dict | None = None,
    separador: str = SEPARADOR_CONSULTAS,
) -> list[ResultadoSql]:
    """Ejecuta una o varias sentencias SQL en una sola transaccion.

    Args:
        sql: una sentencia o varias separadas por ``separador``.
        engine: engine de SQLAlchemy ya construido.
        parametros: valores para los marcadores ``:nombre`` del SQL. Un
            parametro que no aparece en la sentencia se ignora.
        separador: texto que separa las sentencias (por defecto
            ``SEPARADOR_CONSULTAS``).

    Returns:
        Un ``ResultadoSql`` por sentencia, en el orden en que se ejecutaron.

    Raises:
        ValueError: si ``sql`` o ``separador`` estan vacios.
        ExcepcionConexion: no se pudo conectar o la conexion se perdio
            (codigo de salida 2).
        ExcepcionEjecucionSql: la base rechazo una sentencia (codigo 3); la
            transaccion completa queda revertida, sin sentencias a medias.
    """
    sentencias = _dividir(sql, separador)
    if not isinstance(engine, Engine):
        raise ValueError("El parametro 'engine' debe ser un Engine de SQLAlchemy")

    log.debug("Ejecutando %d sentencia(s) sobre %s", len(sentencias), _describir(engine))
    resultados: list[ResultadoSql] = []

    # La conexion se abre aparte: lo que falle aqui es conexion (2); lo que
    # falle dentro de la transaccion es SQL (3). Mezclar ambos casos obliga al
    # consumidor a adivinar por el tipo de excepcion del driver.
    # OSError cubre los fallos de red/DNS que el driver lanza antes de que
    # SQLAlchemy los envuelva (oracledb thin: socket.gaierror).
    try:
        conexion = engine.connect()
    except (SQLAlchemyError, OSError) as exc:
        raise ExcepcionConexion(
            f"No se pudo conectar con la base de datos: {exc}"
        ) from exc

    try:
        with conexion.begin():
            for numero, sentencia in enumerate(sentencias, 1):
                _registrar_encabezado(sentencia)
                valores = _parametros_de(sentencia, parametros)
                try:
                    resultado = conexion.execute(text(sentencia), valores)
                except (SQLAlchemyError, OSError) as exc:
                    if isinstance(exc, (InterfaceError, OSError)) or getattr(
                        exc, "connection_invalidated", False
                    ):
                        raise ExcepcionConexion(
                            f"Se perdio la conexion con la base de datos: {exc}"
                        ) from exc
                    raise ExcepcionEjecucionSql(
                        f"Fallo la sentencia {numero} de {len(sentencias)}: {exc}"
                    ) from exc

                filas = [tuple(fila) for fila in resultado.fetchall()] if resultado.returns_rows else []
                resultados.append(
                    ResultadoSql(
                        sentencia=sentencia,
                        filas=filas,
                        filas_afectadas=None if resultado.returns_rows else resultado.rowcount,
                    )
                )
                log.debug("Sentencia %d de %d ejecutada", numero, len(sentencias))
    finally:
        conexion.close()

    log.info("Bloque de %d sentencia(s) confirmado", len(resultados))
    return resultados


def _dividir(sql: str, separador: str) -> list[str]:
    """Parte el SQL por el separador y descarta lo que quede vacio."""
    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("El SQL a ejecutar no puede estar vacio")
    if not isinstance(separador, str) or not separador.strip():
        raise ValueError("El separador de consultas no puede estar vacio")

    sentencias = [parte.strip() for parte in sql.split(separador)]
    sentencias = [sentencia for sentencia in sentencias if sentencia]
    if not sentencias:
        raise ValueError("El SQL a ejecutar no tiene ninguna sentencia util")
    return sentencias


def _parametros_de(sentencia: str, parametros: dict | None) -> dict:
    """Deja solo los parametros que la sentencia realmente usa."""
    if not parametros:
        return {}
    usados = set(_PATRON_MARCADOR.findall(sentencia))
    return {nombre: valor for nombre, valor in parametros.items() if nombre in usados}


def _registrar_encabezado(sentencia: str) -> None:
    """Registra la linea de comentario con la que arranca la sentencia."""
    primera_linea = sentencia.strip().splitlines()[0].strip()
    if primera_linea.startswith("--"):
        log.info(primera_linea)


def _describir(engine: Engine) -> str:
    """Describe el engine sin exponer la clave."""
    return engine.url.render_as_string(hide_password=True)
