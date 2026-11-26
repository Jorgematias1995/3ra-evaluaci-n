"""
==========================================================================
 Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
 Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
--------------------------------------------------------------------------
 Archivo  : vistas/panel.py
 Propósito: Panel gerencial del ADMINISTRADOR (Actividad 4): indicadores
            globales, costo aprovechado vs. merma por menú y ranking de
            las órdenes con mayor pérdida.
 Librerías: streamlit, pandas
==========================================================================
"""
import pandas as pd
import streamlit as st

from datos import base_datos
from logica import analisis
from seguridad import autenticacion
from vistas import encabezado, formato, graficos


def vista() -> None:
    autenticacion.exigir_permiso("ve_panel")
    encabezado.titulo("Panel gerencial", "gerencia", ancho=130)

    ordenes = base_datos.ordenes()             # sin las anuladas
    if not ordenes:
        st.info("Aún no hay servicios registrados. Cuando cocina registre órdenes, aparecerán aquí.")
        return

    # -- Indicadores clave (KPIs) ---------------------------------------------
    k = analisis.indicadores(ordenes)
    st.caption(f"Actualizado {formato.hora_actual()} · {k['servicios']} servicios pendientes y preparados "
               "(las órdenes anuladas no cuentan).")
    fila1 = st.columns(3)
    fila1[0].metric("Servicios realizados", formato.numero(k["servicios"], 0), border=True)
    fila1[1].metric("Costo total de operación", formato.pesos(k["costo_total"]), border=True,
                    help="Suma de todos los envases abiertos (incluye lo que se perdió).")
    fila1[2].metric("Pérdida total por merma", formato.pesos(k["perdida_total"]), border=True,
                    help="Valor de lo que sobró de los envases abiertos y no se pudo guardar.")
    fila2 = st.columns(3)
    fila2[0].metric("Comensales atendidos", formato.numero(k["comensales"], 0), border=True)
    fila2[1].metric("Ingresos proyectados por venta", formato.pesos(k["ingresos"]), border=True,
                    help="Precio de venta (costo real por plato × 1,25) × comensales.")
    fila2[2].metric("Ganancia proyectada", formato.pesos(k["ganancia"]), border=True)
    st.markdown(f"La merma equivale al **{formato.numero(k['porcentaje_merma'] * 100, 1)} %** "
                "del costo de operación.")

    # -- Costo aprovechado vs. merma por menú ----------------------------------
    st.subheader("Costo por menú: aprovechado y merma")
    por_menu = analisis.totales_por(ordenes, "menu", ("costo_total", "perdida_merma", "venta_total", "comensales"))
    orden_menus = [g["menu"] for g in por_menu]          # ya viene de mayor a menor costo
    largo = []
    for g in por_menu:
        aprovechado = g["costo_total"] - g["perdida_merma"]
        comun = {"menu": g["menu"], "costo_txt": formato.pesos(g["costo_total"]),
                 "merma_txt": formato.pesos(g["perdida_merma"]),
                 "pct_txt": f"{formato.numero(100 * g['perdida_merma'] / g['costo_total'], 1)} %"}
        largo.append({**comun, "parte": "Aprovechado", "orden_parte": 0, "monto": aprovechado})
        largo.append({**comun, "parte": "Merma", "orden_parte": 1, "monto": g["perdida_merma"]})
    tooltip = [("menu", "Menú"), ("costo_txt", "Costo total"), ("merma_txt", "Merma"),
               ("pct_txt", "Merma / costo")]
    st.altair_chart(graficos.barras_apiladas(pd.DataFrame(largo), "menu", orden_menus, tooltip), width="stretch", theme=None)

    with st.expander("Ver la tabla por menú"):
        tabla = pd.DataFrame([{
            "Menú": g["menu"], "Servicios": g["registros"], "Comensales": g["comensales"],
            "Costo total": g["costo_total"], "Pérdida por merma": g["perdida_merma"],
            "Merma / costo": 100 * g["perdida_merma"] / g["costo_total"],
            "Venta total": g["venta_total"],
        } for g in por_menu])
        st.dataframe(formato.tabla_chilena(tabla, montos=("Costo total", "Pérdida por merma", "Venta total"),
                                           porcentajes=("Merma / costo",)), hide_index=True, width="stretch")

    # -- Ranking con cola con prioridad ---------------------------------------
    st.subheader("Órdenes con mayor pérdida por merma")
    st.caption("Las 5 primeras de una cola con prioridad (montículo) ordenada por pérdida.")
    top = analisis.mayores_perdidas(ordenes, 5)
    tabla = pd.DataFrame([{
        "N°": o["id"], "Fecha": formato.fecha_local(o["fecha"]), "Menú": o["menu"],
        "Comensales": o["comensales"], "Pérdida por merma": o["perdida_merma"], "Costo total": o["costo_total"],
    } for o in top])
    st.dataframe(formato.tabla_chilena(tabla, montos=("Pérdida por merma", "Costo total")),
                 hide_index=True, width="stretch")
