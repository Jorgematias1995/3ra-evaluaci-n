"""
==========================================================================
 Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
 Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
--------------------------------------------------------------------------
 Archivo  : vistas/cocina.py
 Propósito: Perfil COCINA (Actividad 3).
              - Formulario de solicitud: menú + comensales, con validación.
              - Orden de preparación: SOLO ingredientes y cantidades.
              - Guardado automático de la orden y su cálculo en Supabase.
              - Cola de preparación (Cola FIFO) y órdenes de la sesión
                (Pila LIFO, con deshacer).
              - Consulta de insumos (búsqueda secuencial + grafo).
 Librerías: streamlit, pandas, fractions (estándar)
==========================================================================

Control de acceso: esta página no muestra costos, pérdidas ni precios. Esos
datos solo aparecen si el rol del usuario tiene ve_costos = true (el
administrador, que también puede usar esta página).
"""
from fractions import Fraction

import pandas as pd
import streamlit as st

from datos import base_datos
from logica import analisis, calculo
from logica.calculo import ErrorValidacion
from logica.estructuras import Cola, Pila
from logica.ordenamiento import (busqueda_secuencial, busqueda_secuencial_todos, normalizar,
                                 ordenamiento_insercion)
from seguridad import autenticacion
from vistas import formato


def vista() -> None:
    sesion = autenticacion.sesion_actual()
    if sesion is None:
        st.stop()
    recetas = base_datos.recetas()
    ingredientes = base_datos.ingredientes()

    st.title("Orden de preparación")
    nueva, cola, mias, insumos = st.tabs(["Nueva orden", "Cola de preparación", "Mis órdenes", "Consultar insumo"])
    with nueva:
        _nueva_orden(recetas, sesion)
    with cola:
        _cola_de_preparacion(ingredientes)
    with mias:
        _ordenes_de_la_sesion()
    with insumos:
        _consultar_insumo(ingredientes, recetas, sesion)


# ==========================================================================
# Nueva orden: formulario -> cálculo -> guardado -> orden de preparación
# ==========================================================================
def _nueva_orden(recetas, sesion) -> None:
    aviso = st.session_state.pop("aviso_orden", None)
    if aviso:
        st.success(aviso)

    with st.form("solicitud"):
        menu = st.selectbox("Menú", [r.nombre for r in recetas], index=None,
                            placeholder="Seleccione el menú")
        # value=None deja el campo vacío para que la validación detecte el nulo;
        # step=1 hace que el campo sea de números enteros.
        comensales = st.number_input("Cantidad de comensales", value=None, step=1, placeholder="Ej.: 25")
        enviar = st.form_submit_button("Calcular y registrar orden", type="primary", width="stretch")

    if enviar:
        _registrar(menu, comensales, recetas, sesion)

    orden = st.session_state.get("ultima_orden")
    if orden is not None:
        _mostrar_orden(orden, sesion)


def _registrar(nombre_menu, comensales, recetas, sesion) -> None:
    """Valida, calcula, guarda y deja la orden lista para mostrarse."""
    errores = []
    receta = None
    if nombre_menu is None:
        errores.append("Seleccione un menú.")
    else:
        receta, _ = busqueda_secuencial(recetas, lambda r: r.nombre == nombre_menu)
    try:
        cantidad = calculo.validar_comensales(comensales)   # nulo, cero, negativo, decimal...
    except ErrorValidacion as error:
        errores.append(str(error))
    if errores:
        for error in errores:
            st.error(error)
        return

    orden = calculo.calcular_orden(receta, cantidad)
    try:
        base_datos.guardar_orden(orden, sesion["usuario"])  # se guarda sola, sin otro botón
    except Exception as error:   # sin conexión, tabla faltante, etc.
        st.error("No se pudo guardar la orden en Supabase. Revise la conexión e intente de nuevo.")
        with st.expander("Detalle técnico"):
            st.code(str(error))
        return

    _pila_sesion().apilar({"id": orden.id, "menu": receta.nombre, "comensales": cantidad,
                           "hora": formato.hora_actual()})
    st.session_state["ultima_orden"] = orden
    st.session_state["aviso_orden"] = (f"Orden N° {orden.id} registrada: {receta.nombre} "
                                       f"para {cantidad} comensales.")
    st.rerun()      # recarga la página con la cola y la pila ya actualizadas


def _mostrar_orden(orden, sesion) -> None:
    st.subheader(f"Orden N° {orden.id} · {orden.receta.nombre}")
    st.caption(f"{orden.comensales} comensales. Retire de bodega los envases completos "
               "y use en la preparación la cantidad indicada.")
    # Inserción: ordena alfabéticamente los 4 o 5 ingredientes (lista muy corta).
    detalles = ordenamiento_insercion(orden.detalles, clave=lambda d: d.ingrediente.nombre)
    st.table(pd.DataFrame({
        "Ingrediente": [d.ingrediente.nombre for d in detalles],
        "Retirar de bodega": [formato.envases(d.ingrediente, d.envases) for d in detalles],
        "Usar en la preparación": [formato.cantidad_fisica(d.ingrediente, d.cantidad_requerida,
                                                           d.porciones_requeridas) for d in detalles],
    }).set_index("Ingrediente"))

    if sesion["ve_costos"]:          # solo administración: el perfil cocina nunca ve esto
        with st.expander("Costos y merma de esta orden (solo administración)"):
            col1, col2 = st.columns(2)
            col1.metric("Costo total", formato.pesos(calculo.a_pesos(orden.costo_total)))
            col2.metric("Pérdida por merma", formato.pesos(calculo.a_pesos(orden.perdida_total)))
            col1.metric("Costo real por plato", formato.pesos(calculo.a_pesos(orden.costo_por_plato)))
            col2.metric("Precio de venta por plato", formato.pesos(calculo.a_pesos(orden.precio_venta_plato)))
            st.table(pd.DataFrame({
                "Ingrediente": [d.ingrediente.nombre for d in detalles],
                "Costo": [formato.pesos(d.costo) for d in detalles],
                "Sobra (merma física)": [formato.cantidad_fisica(d.ingrediente, d.merma_fisica,
                                                                 d.porciones_sobrantes)
                                         if d.porciones_sobrantes else "—" for d in detalles],
                "Pérdida": [formato.pesos(calculo.a_pesos(d.perdida)) for d in detalles],
            }).set_index("Ingrediente"))


# ==========================================================================
# Cola de preparación (FIFO)
# ==========================================================================
def _cola_de_preparacion(ingredientes) -> None:
    aviso = st.session_state.pop("aviso_cola", None)
    if aviso:
        st.success(aviso)

    cola = Cola()
    for fila in base_datos.ordenes_pendientes():    # vienen de la más antigua a la más nueva
        cola.encolar(fila)
    if cola.esta_vacia():
        st.info("No hay órdenes pendientes de preparación.")
        return

    st.caption(f"{len(cola)} órdenes pendientes. Se preparan en orden de llegada: "
               "la primera que entra es la primera que sale.")
    siguiente = cola.frente()
    por_id = {i.id: i for i in ingredientes}
    with st.container(border=True):
        st.markdown(f"**Siguiente: N° {siguiente['id']} · {siguiente['menu']}**")
        st.caption(f"{siguiente['comensales']} comensales · registrada el "
                   f"{formato.fecha_local(siguiente['fecha'])} por {siguiente['usuario']}")
        filas = []
        for insumo in base_datos.detalle_de_orden(siguiente["id"]):
            ingrediente = por_id[insumo["ingrediente_id"]]
            requerida = Fraction(insumo["porciones_requeridas"], ingrediente.rendimiento)
            filas.append({"Ingrediente": ingrediente.nombre,
                          "Retirar de bodega": formato.envases(ingrediente, insumo["envases"]),
                          "Usar en la preparación": formato.cantidad_fisica(
                              ingrediente, requerida, insumo["porciones_requeridas"])})
        if filas:
            filas = ordenamiento_insercion(filas, clave=lambda f: f["Ingrediente"])
            st.table(pd.DataFrame(filas).set_index("Ingrediente"))
        if st.button("Marcar como preparada", type="primary", icon=":material/check_circle:"):
            atendida = cola.desencolar()                 # sale la primera de la fila
            if base_datos.cambiar_estado(atendida["id"], "preparada"):
                st.session_state["aviso_cola"] = f"Orden N° {atendida['id']} marcada como preparada."
            else:
                st.session_state["aviso_cola"] = f"La orden N° {atendida['id']} ya había cambiado de estado."
            st.rerun()

    if len(cola) > 1:
        st.markdown("**En espera**")
        for posicion, fila in enumerate(cola, start=1):
            if posicion > 1:
                st.markdown(f"{posicion}. N° {fila['id']} · {fila['menu']} · {fila['comensales']} comensales")


# ==========================================================================
# Órdenes registradas en esta sesión (Pila: deshacer la última)
# ==========================================================================
def _pila_sesion() -> Pila:
    if "pila_ordenes" not in st.session_state:
        st.session_state["pila_ordenes"] = Pila()
    return st.session_state["pila_ordenes"]


def _ordenes_de_la_sesion() -> None:
    aviso = st.session_state.pop("aviso_pila", None)
    if aviso:
        tipo, texto = aviso
        (st.success if tipo == "ok" else st.error)(texto)

    pila = _pila_sesion()
    if pila.esta_vacia():
        st.info("Aún no registra órdenes en esta sesión.")
        return
    st.caption("La más reciente queda arriba. «Deshacer» anula la última registrada, "
               "solo si todavía no se prepara.")
    for posicion, orden in enumerate(pila):             # de la cima al fondo
        marca = "  ← última" if posicion == 0 else ""
        st.markdown(f"- N° {orden['id']} · {orden['menu']} · {orden['comensales']} comensales · "
                    f"{orden['hora']}{marca}")

    if st.button("Deshacer última orden", icon=":material/undo:"):
        ultima = pila.cima()
        if base_datos.cambiar_estado(ultima["id"], "anulada", solo_si="pendiente"):
            pila.desapilar()
            mostrada = st.session_state.get("ultima_orden")
            if mostrada is not None and mostrada.id == ultima["id"]:
                del st.session_state["ultima_orden"]
            st.session_state["aviso_pila"] = ("ok", f"Orden N° {ultima['id']} anulada.")
        else:
            st.session_state["aviso_pila"] = ("error", f"La orden N° {ultima['id']} ya fue preparada; "
                                                       "no se puede anular.")
        st.rerun()


# ==========================================================================
# Consulta de insumos (búsqueda secuencial + grafo menú-ingrediente)
# ==========================================================================
def _consultar_insumo(ingredientes, recetas, sesion) -> None:
    texto = st.text_input("Nombre del insumo", placeholder="Ej.: papa, huevo, aceite")
    if not texto.strip():
        st.caption(f"Escriba parte del nombre. Hay {len(ingredientes)} insumos en el catálogo.")
        return

    buscado = normalizar(texto)
    encontrados = busqueda_secuencial_todos(ingredientes, lambda i: buscado in normalizar(i.nombre))
    if not encontrados:
        st.warning(f"No hay insumos que contengan «{texto.strip()}».")
        return

    grafo = analisis.grafo_menu_ingrediente(recetas)
    for ingrediente in encontrados:
        with st.container(border=True):
            st.markdown(f"**{ingrediente.nombre}**")
            personas = "persona" if ingrediente.rendimiento == 1 else "personas"
            detalle = (f"Se retira por {ingrediente.unidad_compra}: cada {ingrediente.unidad_compra} rinde "
                       f"{ingrediente.rendimiento} {personas}.")
            if ingrediente.unidades_por_envase and ingrediente.nombre_unidad != "ml":
                detalle += f" Equivale a {ingrediente.unidades_por_envase} {ingrediente.nombre_unidad} (supuesto)."
            st.caption(detalle)
            menus = ordenamiento_insercion(grafo.vecinos(ingrediente.nombre))
            st.markdown("Se usa en: " + (", ".join(menus) if menus else "ningún menú"))
            if sesion["ve_costos"]:
                st.caption(f"Costo: {formato.pesos(ingrediente.costo_envase)} por {ingrediente.unidad_compra} · "
                           f"{formato.pesos(calculo.a_pesos(ingrediente.costo_porcion))} por persona")
