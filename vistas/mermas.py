"""
==========================================================================
 Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
 Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
--------------------------------------------------------------------------
 Archivo  : vistas/mermas.py
 Propósito: Análisis de desechos e impacto económico (Actividad 4):
            qué menús e ingredientes generan más pérdida por merma, para
            apoyar decisiones logísticas.
 Librerías: streamlit, pandas, math (estándar)
==========================================================================

Estructuras usadas: grafo menú-ingrediente (pérdida por par), cola con
prioridad (rankings), árbol binario de búsqueda (consulta por rango de
pérdida) y el motor de cálculo para simular cantidades de comensales.
"""
import math

import pandas as pd
import streamlit as st

from datos import base_datos
from logica import analisis, calculo
from logica.ordenamiento import busqueda_secuencial
from seguridad import autenticacion
from vistas import formato, graficos


def vista() -> None:
    autenticacion.exigir_permiso("ve_panel")
    st.title("Análisis de mermas")
    recetas = base_datos.recetas()
    ordenes = base_datos.ordenes()
    if ordenes:
        _analisis_historico(ordenes, base_datos.detalle_ordenes(), recetas)
    else:
        st.info("Aún no hay órdenes registradas. Mientras tanto, puede usar el simulador.")
    _simulador(recetas)


def _analisis_historico(ordenes, detalle, recetas) -> None:
    por_menu = analisis.totales_por(ordenes, "menu", ("perdida_merma", "costo_total"))
    por_insumo = analisis.totales_por(detalle, "ingrediente", ("perdida_merma", "costo"))
    grafo = analisis.grafo_menu_ingrediente(recetas, detalle)
    total = sum(g["perdida_merma"] for g in por_menu)

    # -- Hallazgo principal ---------------------------------------------------
    if total > 0:
        peor_menu, peor_insumo = por_menu[0], por_insumo[0]
        menus_del_insumo = [(m, grafo.peso(m, peor_insumo["ingrediente"])) for m in grafo.vecinos(peor_insumo["ingrediente"])]
        menu_critico = max(menus_del_insumo, key=lambda par: par[1])[0]
        st.info(f"El insumo que más se pierde es **{peor_insumo['ingrediente']}** "
                f"({formato.pesos(peor_insumo['perdida_merma'])}, "
                f"{formato.numero(100 * peor_insumo['perdida_merma'] / total, 1)} % de la merma), "
                f"sobre todo en **{menu_critico}**. El menú con más pérdida es **{peor_menu['menu']}** "
                f"({formato.pesos(peor_menu['perdida_merma'])}).")
    else:
        st.success("Las órdenes registradas no generaron merma.")

    # -- Pérdida por menú y por insumo ----------------------------------------
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Pérdida por menú")
        df = pd.DataFrame([{"menu": g["menu"], "perdida": g["perdida_merma"],
                            "perdida_txt": formato.pesos(g["perdida_merma"]), "servicios": g["registros"]}
                           for g in por_menu])
        st.altair_chart(graficos.barras(df, "perdida", "menu", [("menu", "Menú"), ("perdida_txt", "Pérdida"),
                                                                ("servicios", "Servicios")]), width="stretch", theme=None)
    with col2:
        st.subheader("Pérdida por insumo")
        df = pd.DataFrame([{"insumo": g["ingrediente"], "perdida": g["perdida_merma"],
                            "perdida_txt": formato.pesos(g["perdida_merma"]),
                            "pct_txt": f"{formato.numero(100 * g['perdida_merma'] / g['costo'], 1)} % de lo comprado"}
                           for g in por_insumo])
        st.altair_chart(graficos.barras(df, "perdida", "insumo", [("insumo", "Insumo"), ("perdida_txt", "Pérdida"),
                                                                  ("pct_txt", "Se pierde")]), width="stretch", theme=None)

    with st.expander("Ver las tablas comparativas"):
        tabla = pd.DataFrame([{
            "Insumo": g["ingrediente"], "Usos en órdenes": g["registros"], "Comprado": g["costo"],
            "Pérdida": g["perdida_merma"], "Se pierde": 100 * g["perdida_merma"] / g["costo"],
            "Menús que lo usan": grafo.grado(g["ingrediente"]),
        } for g in por_insumo])
        st.dataframe(formato.tabla_chilena(tabla, montos=("Comprado", "Pérdida"), porcentajes=("Se pierde",)),
                     hide_index=True, width="stretch")
        tabla = pd.DataFrame([{
            "Menú": g["menu"], "Servicios": g["registros"], "Costo": g["costo_total"],
            "Pérdida": g["perdida_merma"], "Merma / costo": 100 * g["perdida_merma"] / g["costo_total"],
        } for g in por_menu])
        st.dataframe(formato.tabla_chilena(tabla, montos=("Costo", "Pérdida"), porcentajes=("Merma / costo",)),
                     hide_index=True, width="stretch")

    # -- Mapa menú x insumo (pesos de las aristas del grafo) -------------------
    st.subheader("Mapa de pérdidas: menú × insumo")
    st.caption("Cada celda es una arista del grafo menú–insumo y su color, la pérdida acumulada. "
               "Las celdas vacías indican que el menú no usa ese insumo.")
    celdas = [{"menu": m, "ingrediente": i, "perdida": grafo.peso(m, i), "perdida_txt": formato.pesos(grafo.peso(m, i))}
              for m in grafo.vertices("menu") for i in grafo.vecinos(m)]
    st.altair_chart(graficos.mapa_calor(pd.DataFrame(celdas), [("menu", "Menú"), ("ingrediente", "Insumo"),
                                                               ("perdida_txt", "Pérdida")]), width="stretch", theme=None)

    pares = analisis.pares_con_mas_perdida(grafo, 5)
    if pares:
        st.markdown("**Combinaciones que más pierden** (cola con prioridad)")
        tabla = pd.DataFrame([{"Menú": p["menu"], "Insumo": p["ingrediente"], "Pérdida": p["perdida"]} for p in pares])
        st.dataframe(formato.tabla_chilena(tabla, montos=("Pérdida",)), hide_index=True, width="stretch")

    # -- Consulta por rango con el árbol binario de búsqueda -------------------
    st.subheader("Órdenes por rango de pérdida")
    arbol = analisis.arbol_por_perdida(ordenes)
    tope = max(25, int(math.ceil(max(o["perdida_merma"] for o in ordenes) / 25) * 25))
    minimo, maximo = st.slider("Pérdida por orden", 0, tope, (0, tope), step=25, format="$%d")
    encontradas = arbol.rango(minimo, maximo)
    st.caption(f"Árbol binario de búsqueda con {len(arbol)} órdenes y {arbol.altura()} niveles: "
               f"{len(encontradas)} órdenes en el rango, de menor a mayor pérdida (recorrido inorden).")
    if encontradas:
        tabla = pd.DataFrame([{"N°": o["id"], "Fecha": formato.fecha_local(o["fecha"]), "Menú": o["menu"],
                               "Comensales": o["comensales"], "Pérdida": o["perdida_merma"]} for o in encontradas])
        st.dataframe(formato.tabla_chilena(tabla, montos=("Pérdida",)), hide_index=True, width="stretch",
                     height=min(38 + 35 * len(tabla), 460))


def _simulador(recetas) -> None:
    st.subheader("Simulador: ¿con cuántos comensales se pierde menos?")
    st.caption("Calcula cada menú de 1 a 60 comensales sin guardar nada. Los puntos azules marcan "
               "las cantidades sin merma (todos los envases se usan completos).")
    nombre = st.selectbox("Menú a simular", [r.nombre for r in recetas], key="menu_simulado")
    receta, _ = busqueda_secuencial(recetas, lambda r: r.nombre == nombre)
    filas = calculo.simular_comensales(receta, 1, 60)
    for fila in filas:
        fila["perdida_txt"] = formato.pesos(round(fila["perdida_por_plato"], 2))
        fila["costo_txt"] = formato.pesos(round(fila["costo_por_plato"], 2))
    st.altair_chart(graficos.linea_simulacion(pd.DataFrame(filas)), width="stretch", theme=None)
    mcm = calculo.comensales_sin_merma(receta)
    st.markdown(f"**{receta.nombre}** no genera merma con **{mcm} comensales** o sus múltiplos "
                f"(mínimo común múltiplo de lo que rinde cada insumo). Si el servicio se acerca a esa "
                f"cantidad, conviene ajustar el grupo o combinarlo con otro menú que use los mismos insumos.")
