"""
==========================================================================
 Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
 Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
--------------------------------------------------------------------------
 Archivo  : seguridad/autenticacion.py
 Propósito: Identificar al usuario y controlar qué puede ver (Actividad 3).
 Librerías: streamlit (session_state), time (estándar)
==========================================================================

Mecanismo:
1. Los usuarios están en la tabla `usuarios` de Supabase, con su rol y el
   hash de su contraseña. Los permisos de cada rol (ve_costos, ve_panel)
   están en la tabla `roles`.
2. Al ingresar, se busca el nombre de usuario en la lista con BÚSQUEDA
   SECUENCIAL y se verifica la contraseña contra el hash guardado.
3. Si es correcta, el usuario y sus permisos quedan en st.session_state
   (memoria de la sesión de ese navegador). app.py arma el menú solo con las
   páginas permitidas, y cada página de administración vuelve a revisar el
   permiso (por si alguien escribe la dirección a mano).
4. Tras 5 intentos fallidos el ingreso se bloquea 30 segundos en esa
   sesión del navegador.
"""
from __future__ import annotations

import time

import streamlit as st

from datos import base_datos
from logica.ordenamiento import busqueda_secuencial
from seguridad.claves import hash_ficticio, verificar_clave

CLAVE_SESION = "sesion"
MAX_INTENTOS = 5
SEGUNDOS_BLOQUEO = 30


def segundos_bloqueado() -> int:
    """Segundos que faltan para poder intentar de nuevo (0 si no hay bloqueo)."""
    hasta = st.session_state.get("bloqueado_hasta", 0)
    return max(0, int(hasta - time.time()))


def iniciar_sesion(nombre_usuario: str, clave: str) -> dict | None:
    """Devuelve la sesión si el usuario y la contraseña son correctos; si no, None."""
    nombre = (nombre_usuario or "").strip().lower()
    if not nombre or not clave or segundos_bloqueado() > 0:
        return None

    lista = base_datos.usuarios()
    encontrado, _comparaciones = busqueda_secuencial(lista, lambda u: u["usuario"] == nombre)

    if encontrado is None:
        verificar_clave(clave, hash_ficticio())     # mismo tiempo exista o no el usuario
        valido = False
    else:
        valido = encontrado["activo"] and verificar_clave(clave, encontrado["clave_hash"])

    if not valido:
        intentos = st.session_state.get("intentos_fallidos", 0) + 1
        st.session_state["intentos_fallidos"] = intentos
        if intentos >= MAX_INTENTOS:
            st.session_state["bloqueado_hasta"] = time.time() + SEGUNDOS_BLOQUEO
            st.session_state["intentos_fallidos"] = 0
        return None

    permisos = encontrado.get("roles") or {}
    sesion = {
        "usuario": encontrado["usuario"],
        "nombre": encontrado["nombre"],
        "rol": encontrado["rol"],
        "ve_costos": bool(permisos.get("ve_costos")),   # costos, mermas en $, precios
        "ve_panel": bool(permisos.get("ve_panel")),     # panel, historial y análisis
    }
    st.session_state[CLAVE_SESION] = sesion
    st.session_state["intentos_fallidos"] = 0
    return sesion


def sesion_actual() -> dict | None:
    return st.session_state.get(CLAVE_SESION)


def cerrar_sesion() -> None:
    """Borra todo lo guardado en la sesión (usuario, órdenes de la sesión, filtros)."""
    for clave in list(st.session_state.keys()):
        del st.session_state[clave]


def exigir_permiso(permiso: str) -> dict:
    """Detiene la página si el usuario no tiene el permiso. Defensa extra:
    el menú ya oculta estas páginas, pero así tampoco se abren a mano."""
    sesion = sesion_actual()
    if not sesion or not sesion.get(permiso):
        st.error("No tiene permiso para ver esta página.")
        st.stop()
    return sesion
