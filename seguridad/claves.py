"""
==========================================================================
 Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
 Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
--------------------------------------------------------------------------
 Archivo  : seguridad/claves.py
 Propósito: Guardar contraseñas de forma segura (nunca en texto plano).
 Librerías: hashlib, hmac, os, functools (biblioteca estándar)
==========================================================================

Formato guardado en usuarios.clave_hash:
    pbkdf2_sha256$<iteraciones>$<sal en hex>$<hash en hex>

* PBKDF2 aplica SHA-256 200.000 veces: adivinar claves por fuerza bruta se
  vuelve muy lento.
* La sal (16 bytes al azar, distinta por usuario) hace que dos claves iguales
  tengan hashes distintos.
* hmac.compare_digest compara en tiempo constante (no revela cuántos
  caracteres coincidieron).
"""
from __future__ import annotations

import hashlib
import hmac
import os
from functools import lru_cache

ALGORITMO = "pbkdf2_sha256"
ITERACIONES = 200_000


def generar_hash(clave: str, iteraciones: int = ITERACIONES) -> str:
    sal = os.urandom(16)
    resultado = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), sal, iteraciones)
    return f"{ALGORITMO}${iteraciones}${sal.hex()}${resultado.hex()}"


def verificar_clave(clave: str, guardado: str) -> bool:
    """Recalcula el hash con la misma sal e iteraciones y lo compara."""
    try:
        algoritmo, iteraciones, sal_hex, hash_hex = guardado.split("$")
        if algoritmo != ALGORITMO:
            return False
        calculado = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"),
                                        bytes.fromhex(sal_hex), int(iteraciones))
        return hmac.compare_digest(calculado, bytes.fromhex(hash_hex))
    except (ValueError, AttributeError):    # hash con formato inválido
        return False


@lru_cache(maxsize=1)
def hash_ficticio() -> str:
    """Hash de relleno: si el usuario no existe se verifica contra este, para
    que la respuesta tarde lo mismo y no delate qué usuarios existen."""
    return generar_hash(os.urandom(16).hex())
