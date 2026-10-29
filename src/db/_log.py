"""Configuracion de logging para los entrypoints de la libreria.

La libreria solo emite: cada modulo usa ``logging.getLogger(__name__)`` y el
paquete agrega un ``NullHandler``. El que configura de verdad es el entrypoint
(los tests de este repo). Si el proyecto consumidor no configura logging, los
mensajes de la libreria no se imprimen y no se crea ningun archivo: eso es
correcto.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

CARPETA_LOGS = Path(__file__).resolve().parents[2] / "logs"
NIVEL_POR_DEFECTO = "INFO"
FORMATO = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def configurar_log(
    nivel: str | None = None,
    prefijo: str = "db-",
    conservar: int = 30,
) -> Path:
    """Configura archivo + consola en el logger raiz y devuelve el archivo creado.

    Args:
        nivel: DEBUG, INFO, WARNING o ERROR. Si no se envia, se lee de la
            variable de entorno ``DB_NIVEL_LOG`` y, si tampoco esta, INFO.
        prefijo: prefijo de los archivos de log.
        conservar: cuantos archivos de log se mantienen en ``logs/``.

    Returns:
        Ruta del archivo de log de esta corrida.
    """
    nivel_efectivo = (nivel or os.getenv("DB_NIVEL_LOG") or NIVEL_POR_DEFECTO).upper()
    valor_numerico = getattr(logging, nivel_efectivo, None)
    if not isinstance(valor_numerico, int):
        raise ValueError(
            f"Nivel de log invalido: {nivel_efectivo!r}. Use DEBUG, INFO, WARNING o ERROR."
        )

    CARPETA_LOGS.mkdir(parents=True, exist_ok=True)
    purgar_logs(prefijo=prefijo, conservar=conservar)
    archivo = CARPETA_LOGS / f"{prefijo}{datetime.now():%Y%m%d-%H%M%S-%f}.log"

    formato = logging.Formatter(FORMATO)
    raiz = logging.getLogger()
    raiz.setLevel(valor_numerico)
    for manejador in list(raiz.handlers):
        raiz.removeHandler(manejador)

    manejador_archivo = logging.FileHandler(archivo, encoding="utf-8")
    manejador_archivo.setFormatter(formato)
    raiz.addHandler(manejador_archivo)

    manejador_consola = logging.StreamHandler()
    manejador_consola.setFormatter(formato)
    raiz.addHandler(manejador_consola)

    return archivo


def purgar_logs(prefijo: str = "db-", conservar: int = 30) -> list[Path]:
    """Borra los logs mas antiguos y deja los ``conservar`` mas recientes."""
    if conservar <= 0:
        raise ValueError("La cantidad de logs a conservar debe ser mayor que cero")
    if not CARPETA_LOGS.exists():
        return []

    archivos = sorted(
        CARPETA_LOGS.glob(f"{prefijo}*.log"),
        key=lambda ruta: ruta.stat().st_mtime,
        reverse=True,
    )
    borrados = []
    for archivo in archivos[conservar:]:
        archivo.unlink(missing_ok=True)
        borrados.append(archivo)
    return borrados
