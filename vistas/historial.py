"""
==========================================================================
 Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
 Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
--------------------------------------------------------------------------
 Archivo  : vistas/historial.py
 Propósito: Historial completo de órdenes para el ADMINISTRADOR (Actividad 4):
            filtros por menú y estado, orden por columna (merge sort),
            desglose de una orden y exportación con ordenamiento externo.
 Librerías: streamlit, pandas, fractions (estándar)
==========================================================================
"""
from fractions import Fraction

import pandas as pd
import streamlit as st

from datos import base_datos
from logica.ordenamiento import busqueda_secuencial_todos, merge_sort, ordenamiento_externo
from seguridad import autenticacion
from vistas import formato

# Columna visible -> campo del registro por el que se ordena
CAMPOS_ORDEN = {
    "Fecha": "fecha",
    "Pérdida por merma": "perdida_merma",
    "Costo por plato": "costo_por_plato",
    "Costo total": "costo_total",
    "Venta total": "venta_total",
    "Comensales": "comensales",
    "Menú": "menu",
}
ESTADOS = ["pendiente", "preparada", "anulada"]
MONTOS = ("Costo total", "Costo por plato", "Pérdida por merma", "Precio venta por plato", "Venta total")


def vista() -> None:
    autenticacion.exigir_permiso("ve_panel")
    st.title("Historial de preparaciones")

    ordenes = base_datos.ordenes(incluir_anuladas=True)
    if not ordenes:
        st.info("Aún no hay órdenes registradas.")
        return
    detalle = base_datos.detalle_ordenes(incluir_anuladas=True)
    catalogo = {i.nombre: i for i in base_datos.ingredientes()}

    # -- Filtros y orden (una fila sobre la tabla) -----------------------------
    col1, col2 = st.columns(2)
    menus = col1.multiselect("Menú", sorted({o["menu"] for o in ordenes}), placeholder="Todos los menús")
    estados = col2.multiselect("Estado", ESTADOS, default=["pendiente", "preparada"],
                               placeholder="Todos los estados")
    col3, col4 = st.columns(2)
    campo = col3.selectbox("Ordenar por", list(CAMPOS_ORDEN))
    descendente = col4.radio("Sentido", ["Mayor a menor", "Menor a mayor"], horizontal=True) == "Mayor a menor"

    # Filtro: recorrido secuencial que conserva las órdenes que cumplen ambos criterios.
    filtradas = busqueda_secuencial_todos(
        ordenes, lambda o: (not menus or o["menu"] in menus) and (not estados or o["estado"] in estados))
    # Orden: merge sort (estable, O(n log n)) por la columna elegida.
    ordenadas = merge_sort(filtradas, clave=lambda o: o[CAMPOS_ORDEN[campo]], descendente=descendente)

    if not ordenadas:
        st.warning("Ninguna orden cumple los filtros.")
        return
    st.markdown(f"**{len(ordenadas)} órdenes** · costo {formato.pesos(sum(o['costo_total'] for o in ordenadas))}"
                f" · pérdida por merma {formato.pesos(sum(o['perdida_merma'] for o in ordenadas))}"
                f" · venta {formato.pesos(sum(o['venta_total'] for o in ordenadas))}")

    # Merma física de cada orden, en texto corto ("Papa 0,5 kg · Huevo 0,17 empaques")
    merma_por_orden = {}
    for fila in detalle:
        if fila["porciones_sobrantes"] > 0:
            ingrediente = catalogo.get(fila["ingrediente"])
            unidad = formato.unidad(ingrediente, fila["merma_fisica"]) if ingrediente else fila["unidad_compra"]
            merma_por_orden.setdefault(fila["orden_id"], []).append(
                f"{fila['ingrediente']} {formato.numero(fila['merma_fisica'])} {unidad}")

    tabla = pd.DataFrame([{
        "N°": o["id"],
        "Fecha": formato.fecha_local(o["fecha"]),
        "Menú": o["menu"],
        "Comensales": o["comensales"],
        "Costo total": o["costo_total"],
        "Costo por plato": o["costo_por_plato"],
        "Merma física": " · ".join(merma_por_orden.get(o["id"], [])) or "Sin merma",
        "Pérdida por merma": o["perdida_merma"],
        "Precio venta por plato": o["precio_venta_plato"],
        "Venta total": o["venta_total"],
        "Estado": o["estado"],
        "Registró": o["usuario"],
    } for o in ordenadas])
    st.dataframe(formato.tabla_chilena(tabla, montos=MONTOS), hide_index=True, width="stretch",
                 height=min(38 + 35 * len(tabla), 460))

    _desglose(ordenadas, detalle, catalogo)
    _exportar(ordenadas)


def _desglose(ordenadas, detalle, catalogo) -> None:
    st.subheader("Desglose de una orden")
    etiquetas = {o["id"]: f"N° {o['id']} · {o['menu']} · {o['comensales']} comensales · "
                          f"{formato.fecha_local(o['fecha'])}" for o in ordenadas}
    elegida = st.selectbox("Orden", list(etiquetas), format_func=etiquetas.get)
    filas = busqueda_secuencial_todos(detalle, lambda d: d["orden_id"] == elegida)
    tabla = []
    for fila in filas:
        ingrediente = catalogo.get(fila["ingrediente"])
        if ingrediente:
            merma = (formato.cantidad_fisica(ingrediente, Fraction(fila["porciones_sobrantes"], ingrediente.rendimiento),
                                             fila["porciones_sobrantes"]) if fila["porciones_sobrantes"] else "—")
        else:
            merma = f"{formato.numero(fila['merma_fisica'])} {fila['unidad_compra']}"
        tabla.append({"Ingrediente": fila["ingrediente"],
                      "Porciones requeridas": fila["porciones_requeridas"],
                      "Envases abiertos": fila["envases"],
                      "Porciones sobrantes": fila["porciones_sobrantes"],
                      "Merma física": merma,
                      "Costo": fila["costo"],
                      "Pérdida": fila["perdida_merma"]})
    st.dataframe(formato.tabla_chilena(pd.DataFrame(tabla), montos=("Costo", "Pérdida")),
                 hide_index=True, width="stretch")


def _exportar(ordenadas) -> None:
    st.subheader("Exportar historial ordenado")
    st.caption("Ordenamiento externo: los registros se ordenan por bloques que se guardan en archivos "
               "temporales (corridas) y luego se mezclan leyendo un registro de cada archivo con una "
               "cola con prioridad. Es la técnica para ordenar historiales que no caben en memoria.")
    col1, col2, col3 = st.columns(3)
    campo = col1.selectbox("Ordenar por", list(CAMPOS_ORDEN), index=1, key="campo_externo")
    bloque = col2.number_input("Registros por bloque", min_value=2, max_value=500, value=10, step=1)
    descendente = col3.radio("Sentido", ["Mayor a menor", "Menor a mayor"], key="sentido_externo") == "Mayor a menor"

    if st.button("Ordenar y preparar archivo", icon=":material/sort:"):
        registros = [{c: o[c] for c in ("id", "fecha", "menu", "comensales", "costo_total", "costo_por_plato",
                                         "perdida_merma", "precio_venta_plato", "venta_total", "estado", "usuario")}
                     for o in ordenadas]
        resultado = ordenamiento_externo(registros, CAMPOS_ORDEN[campo], tam_bloque=int(bloque),
                                         descendente=descendente)
        tabla = pd.DataFrame(resultado.registros)
        tabla["fecha"] = tabla["fecha"].map(formato.fecha_local)
        # ';' y coma decimal: así lo abre directo Excel configurado en español (Chile).
        st.session_state["exportacion"] = {
            "csv": tabla.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
            "texto": (f"{len(resultado.registros)} registros ordenados por {campo.lower()} "
                      f"({'mayor a menor' if descendente else 'menor a mayor'}) en {resultado.corridas} "
                      f"corridas de hasta {resultado.tam_bloque} registros."),
        }

    exportacion = st.session_state.get("exportacion")
    if exportacion:
        st.success(exportacion["texto"])
        st.download_button("Descargar CSV", exportacion["csv"], file_name="historial_ordenado.csv",
                           mime="text/csv", icon=":material/download:")
