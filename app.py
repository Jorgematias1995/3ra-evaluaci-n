"""
==========================================================================
 EVALUACIÓN N°3 · PROGRAMACIÓN AVANZADA (sumativa 30 %)
 Academia Politécnica Militar · División Educación
 Curso y mención : I CRIM Sistemas de Armas
 Profesor        : Dr. Carlos Santibáñez Rodríguez
 Alumno          : Jorge Gómez Prado
 Fecha           : 26 de noviembre de 2026
--------------------------------------------------------------------------
 Sistema         : Gestión de cocina del local «Noches alegres, mañanas tristes»
                   (insumos, mermas, costos y precio de venta)
 Archivo         : app.py (punto de entrada)
 Ejecutar        : streamlit run app.py
 Librerías       : streamlit (interfaz), supabase (base de datos en la nube),
                   pandas (tablas), altair (gráficos), tzdata (hora de Chile
                   en Windows) y la biblioteca estándar de Python (math,
                   fractions, collections, hashlib, json, tempfile...).
                   Versiones mínimas en requirements.txt.
--------------------------------------------------------------------------
 Qué hace
   Cocina ingresa el menú y la cantidad de comensales. El sistema calcula
   los envases completos de cada ingrediente (productos indivisibles que no
   se pueden guardar), la merma y su costo, el costo real por plato y el
   precio de venta con 25 % de ganancia, y guarda todo en Supabase.
   - Perfil 'cocina': solo ve ingredientes y cantidades (sin costos).
   - Perfil 'administrador': acceso total (panel, historial, mermas).

 Estructura (lógica, datos e interfaz separados)
   app.py        ingreso, sesión y menú según el rol (este archivo)
   logica/       cálculo, clases, estructuras de datos y algoritmos
   datos/        consultas a Supabase
   seguridad/    contraseñas (hash) y control de acceso
   vistas/       páginas de Streamlit
   assets/       imágenes de las páginas (gerencia y cocina)
   sql/          creación de tablas y datos iniciales
   scripts/      creación de usuarios
   tests/        pruebas de la lógica

 Credenciales: la URL y la secret key de Supabase están en
 .streamlit/secrets.toml, que NO se sube a GitHub (.gitignore).
==========================================================================

Navegación condicional: st.navigation() recibe SOLO las páginas que el rol
puede ver. Antes de ingresar existe una sola página (ingreso); después, el
menú lateral se arma con los permisos guardados en st.session_state.
"""
import streamlit as st

from seguridad import autenticacion
from vistas import NOMBRE_LOCAL, catalogo, cocina, historial, ingreso, mermas, panel

sesion = autenticacion.sesion_actual()

# El panel del administrador usa todo el ancho; cocina, una columna cómoda en el celular.
st.set_page_config(page_title=f"{NOMBRE_LOCAL} · Cocina", page_icon=":material/nightlife:",
                   layout="wide" if sesion and sesion["ve_panel"] else "centered")

if sesion is None:
    # Sin sesión: la única página que existe es la de ingreso.
    st.navigation([st.Page(ingreso.vista, title="Ingreso", icon=":material/login:")],
                  position="hidden").run()
    st.stop()

# -- Páginas según los permisos del rol ---------------------------------------
pagina_cocina = st.Page(cocina.vista, title="Orden de preparación", icon=":material/skillet:", url_path="cocina")
if sesion["ve_panel"]:
    paginas = {
        "Administración": [
            st.Page(panel.vista, title="Panel gerencial", icon=":material/monitoring:", url_path="panel",
                    default=True),
            st.Page(historial.vista, title="Historial", icon=":material/table_view:", url_path="historial"),
            st.Page(mermas.vista, title="Análisis de mermas", icon=":material/delete_sweep:", url_path="mermas"),
            st.Page(catalogo.vista, title="Catálogo y supuestos", icon=":material/menu_book:", url_path="catalogo"),
        ],
        "Cocina": [pagina_cocina],
    }
else:
    paginas = {"Cocina": [pagina_cocina]}

with st.sidebar:
    st.markdown(f"**{NOMBRE_LOCAL}**")
    st.caption("Gestión de cocina: insumos y mermas")
    st.divider()
    st.markdown(f"**{sesion['nombre']}**")
    st.caption(f"Usuario: {sesion['usuario']} · Perfil: {sesion['rol']}")
    if st.button("Cerrar sesión", icon=":material/logout:", width="stretch"):
        autenticacion.cerrar_sesion()
        st.rerun()

st.navigation(paginas).run()
