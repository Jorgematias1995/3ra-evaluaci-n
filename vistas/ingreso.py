"""
==========================================================================
 Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
 Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
--------------------------------------------------------------------------
 Archivo  : vistas/ingreso.py
 Propósito: Página de ingreso (usuario y contraseña).
 Librerías: streamlit
==========================================================================
"""
import streamlit as st

from seguridad import autenticacion
from vistas import NOMBRE_LOCAL


def vista() -> None:
    st.title(NOMBRE_LOCAL)
    st.caption("Gestión de cocina: insumos y mermas. Cocina ve la orden de preparación; "
               "administración ve además costos, mermas e historial.")

    espera = autenticacion.segundos_bloqueado()
    if espera:
        st.warning(f"Demasiados intentos fallidos. Espere {espera} segundos antes de volver a intentar.")

    # st.form: los datos se envían juntos al presionar el botón (no en cada tecla).
    with st.form("ingreso"):
        usuario = st.text_input("Usuario", placeholder="cocina o administrador")
        clave = st.text_input("Contraseña", type="password")
        entrar = st.form_submit_button("Ingresar", type="primary", width="stretch")

    if entrar:
        if not usuario.strip() or not clave:
            st.error("Ingrese usuario y contraseña.")
        elif autenticacion.iniciar_sesion(usuario, clave):
            st.rerun()                      # app.py vuelve a armar el menú según el rol
        elif autenticacion.segundos_bloqueado():
            st.error(f"Demasiados intentos fallidos. Espere {autenticacion.segundos_bloqueado()} segundos.")
        else:
            # Mensaje genérico: no revela si falló el usuario o la contraseña.
            st.error("Usuario o contraseña incorrectos.")
