"""
==========================================================================
 Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
 Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
--------------------------------------------------------------------------
 Archivo  : vistas/graficos.py
 Propósito: Gráficos del administrador con un mismo estilo (Altair).
 Librerías: altair, pandas
==========================================================================

Criterios de diseño:
* La MERMA siempre es naranja y el costo APROVECHADO siempre azul, en todos
  los gráficos: el color identifica la cosa, no su posición en un ranking.
* Barras delgadas ordenadas de mayor a menor, ejes y grilla tenues.
* Cada gráfico tiene tooltip (al pasar el mouse) y su tabla equivalente en
  la página, para que ningún valor dependa solo del color.
* Montos con formato chileno en los ejes ($1.000).
* Las vistas los muestran con st.altair_chart(..., theme=None): el estilo
  completo está aquí y no se mezcla con el tema de Streamlit.
* Las barras apiladas usan un alto por fila (alt.Step): no se enciman
  aunque haya solo 1 o 2 menús.
"""
import altair as alt
import pandas as pd

AZUL = "#2a78d6"            # costo aprovechado
NARANJA = "#eb6834"         # merma
TINTA = "#52514e"
GRILLA = "#e1e0d9"
EJE = "#c3c2b7"
FUENTE = "Source Sans Pro, Source Sans 3, sans-serif"   # la misma letra de Streamlit

# Etiquetas del eje en pesos chilenos: 12,500 -> $12.500
_PESOS = "'$' + replace(format(datum.value, ',.0f'), regexp(',', 'g'), '.')"


def _tooltips(pares):
    """[(campo, título), ...] -> tooltips de texto (los montos ya vienen formateados)."""
    return [alt.Tooltip(f"{campo}:N", title=titulo) for campo, titulo in pares]


def _eje_pesos(titulo=None):
    return alt.Axis(title=titulo, labelExpr=_PESOS, tickCount=5, grid=True)


def _estilo(grafico):
    return (grafico
            .configure(font=FUENTE)
            .configure_axis(gridColor=GRILLA, domainColor=EJE, tickColor=EJE, labelColor=TINTA,
                            titleColor=TINTA, labelFontSize=12, titleFontSize=12, titleFontWeight="normal")
            .configure_view(strokeWidth=0)
            .configure_legend(labelColor=TINTA, titleColor=TINTA, labelFontSize=12, orient="top"))


def barras(df: pd.DataFrame, valor: str, categoria: str, tooltip: list, titulo_eje=None,
           color: str = NARANJA) -> alt.Chart:
    """Barras horizontales de una sola serie, de mayor a menor."""
    grafico = (alt.Chart(df)
               .mark_bar(color=color, size=18, cornerRadiusEnd=4)
               .encode(x=alt.X(f"{valor}:Q", axis=_eje_pesos(titulo_eje)),
                       y=alt.Y(f"{categoria}:N", sort="-x", title=None, axis=alt.Axis(labelLimit=280)),
                       tooltip=_tooltips(tooltip))
               .properties(height=34 * len(df) + 30))
    return _estilo(grafico)


def barras_apiladas(df: pd.DataFrame, categoria: str, orden_categorias: list, tooltip: list) -> alt.Chart:
    """Barras apiladas 'Aprovechado' + 'Merma' por categoría (columnas: parte, monto)."""
    grafico = (alt.Chart(df)
               .mark_bar(size=18, stroke="white", strokeWidth=2)
               .encode(x=alt.X("monto:Q", stack="zero", axis=_eje_pesos("Costo de los envases abiertos")),
                       y=alt.Y(f"{categoria}:N", sort=orden_categorias, title=None,
                               axis=alt.Axis(labelLimit=280)),
                       color=alt.Color("parte:N", title=None,
                                       scale=alt.Scale(domain=["Aprovechado", "Merma"], range=[AZUL, NARANJA])),
                       order=alt.Order("orden_parte:Q"),
                       tooltip=_tooltips(tooltip))
               # Alto por fila (34 px por menú) y ancho ajustado a la página: con un
               # alto fijo, la leyenda y los ejes se comen el espacio y con 1 o 2
               # menús las barras quedan encimadas.
               .properties(height=alt.Step(34),
                           autosize=alt.AutoSizeParams(type="fit-x", contains="padding")))
    return _estilo(grafico)


def mapa_calor(df: pd.DataFrame, tooltip: list) -> alt.Chart:
    """Pérdida acumulada por par menú-ingrediente (columnas: menu, ingrediente, perdida).
    Una sola tonalidad: más oscuro = más pérdida. Celdas vacías = el menú no usa ese insumo."""
    grafico = (alt.Chart(df)
               .mark_rect(cornerRadius=3, stroke="white", strokeWidth=2)
               .encode(x=alt.X("ingrediente:N", title=None, axis=alt.Axis(labelAngle=-35, labelLimit=120)),
                       y=alt.Y("menu:N", title=None, axis=alt.Axis(labelLimit=280)),
                       color=alt.Color("perdida:Q", title="Pérdida ($)",
                                       scale=alt.Scale(scheme="oranges"),
                                       legend=alt.Legend(labelExpr=_PESOS, gradientLength=220)),
                       tooltip=_tooltips(tooltip))
               .properties(height=36 * df["menu"].nunique() + 40))
    return _estilo(grafico)


def linea_simulacion(df: pd.DataFrame) -> alt.Chart:
    """Pérdida por plato según la cantidad de comensales, con guía al pasar el mouse."""
    base = alt.Chart(df).encode(x=alt.X("comensales:Q", title="Comensales",
                                        axis=alt.Axis(tickMinStep=1, format="d")))
    cercano = alt.selection_point(nearest=True, on="pointerover", fields=["comensales"], empty=False)
    linea = base.mark_line(color=NARANJA, strokeWidth=2).encode(
        y=alt.Y("perdida_por_plato:Q", axis=_eje_pesos("Pérdida por plato")))
    sin_merma = base.transform_filter("datum.perdida_total == 0").mark_point(
        filled=True, size=90, color=AZUL, stroke="white", strokeWidth=2).encode(y="perdida_por_plato:Q")
    guia = base.mark_rule(color=EJE).encode(
        opacity=alt.condition(cercano, alt.value(1), alt.value(0)),
        tooltip=[alt.Tooltip("comensales:Q", title="Comensales"),
                 alt.Tooltip("perdida_txt:N", title="Pérdida por plato"),
                 alt.Tooltip("costo_txt:N", title="Costo por plato")]).add_params(cercano)
    punto = linea.mark_point(filled=True, size=70, color=NARANJA).encode(
        opacity=alt.condition(cercano, alt.value(1), alt.value(0)))
    return _estilo(alt.layer(linea, sin_merma, guia, punto).properties(height=300))
