"""
==========================================================================
 Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
 Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
--------------------------------------------------------------------------
 Archivo  : vistas/catalogo.py
 Propósito: Catálogo para el ADMINISTRADOR: ingredientes con sus costos,
            recetas tal como las da el enunciado y supuestos del cálculo.
 Librerías: streamlit, pandas
==========================================================================
"""
import pandas as pd
import streamlit as st

from datos import base_datos
from logica import analisis, calculo
from logica.ordenamiento import busqueda_secuencial, busqueda_secuencial_todos, normalizar
from logica.supuestos import SUPUESTOS
from seguridad import autenticacion
from vistas import formato


def vista() -> None:
    autenticacion.exigir_permiso("ve_panel")
    st.title("Catálogo y supuestos")
    ingredientes = base_datos.ingredientes()
    recetas = base_datos.recetas()
    pestana_ing, pestana_rec, pestana_sup = st.tabs(["Ingredientes", "Recetas", "Supuestos del cálculo"])

    with pestana_ing:
        texto = st.text_input("Buscar insumo", placeholder="Ej.: pollo")
        lista = (busqueda_secuencial_todos(ingredientes, lambda i: normalizar(texto) in normalizar(i.nombre))
                 if texto.strip() else ingredientes)
        if not lista:
            st.warning(f"No hay insumos que contengan «{texto.strip()}».")
        else:
            # st.table: tabla fija que ajusta el texto largo de las notas en varias líneas.
            st.table(pd.DataFrame([{
                "Ingrediente": i.nombre,
                "Se compra por": i.unidad_compra,
                "Costo del envase": formato.pesos(i.costo_envase),
                "Rinde (personas)": i.rendimiento,
                "Costo por persona": formato.pesos(calculo.a_pesos(i.costo_porcion)),
                "Equivalencia": (f"1 {i.unidad_compra} = {formato.numero(i.unidades_por_envase)} {i.nombre_unidad}"
                                 if i.unidades_por_envase else ""),
                "Nota": i.supuesto or "",
            } for i in lista]).set_index("Ingrediente"))

    with pestana_rec:
        nombre = st.selectbox("Receta", [r.nombre for r in recetas])
        receta, _ = busqueda_secuencial(recetas, lambda r: r.nombre == nombre)
        if receta.observacion:
            st.warning(receta.observacion)
        base = calculo.calcular_orden(receta, receta.comensales_base)
        por_nombre = {d.ingrediente.nombre: d for d in base.detalles}
        tabla = pd.DataFrame([{
            "Ingrediente": linea.ingrediente.nombre,
            f"Receta ({receta.comensales_base} comensales)": f"{formato.numero(linea.cantidad_base)} {linea.unidad_receta}",
            "Rinde por envase (personas)": linea.ingrediente.rendimiento,
            f"Envases para {receta.comensales_base} (tabla)": formato.envases(linea.ingrediente,
                                                                            por_nombre[linea.ingrediente.nombre].envases),
            "Costo": por_nombre[linea.ingrediente.nombre].costo,
        } for linea in receta.lineas])
        st.dataframe(formato.tabla_chilena(tabla, montos=("Costo",)), hide_index=True, width="stretch")
        st.caption(f"Para {receta.comensales_base} comensales: costo {formato.pesos(base.costo_total)}, "
                   f"{formato.pesos(calculo.a_pesos(base.costo_por_plato))} por plato, venta "
                   f"{formato.pesos(calculo.a_pesos(base.precio_venta_plato))} por plato.")
        grafo = analisis.grafo_menu_ingrediente(recetas)
        relacionados = analisis.menus_relacionados(grafo, receta.nombre)
        st.markdown("**Menús que comparten insumos con este** (grafo menú–ingrediente, a 2 saltos): "
                    + (", ".join(relacionados) if relacionados else "ninguno"))
        st.markdown(f"**Sin merma con:** {calculo.comensales_sin_merma(receta)} comensales o sus múltiplos.")

    with pestana_sup:
        for supuesto in SUPUESTOS:
            st.markdown(f"- {supuesto}")
