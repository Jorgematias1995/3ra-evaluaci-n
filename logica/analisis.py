"""
==========================================================================
 Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
 Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
--------------------------------------------------------------------------
 Archivo  : logica/analisis.py
 Propósito: Indicadores y análisis para el administrador (Actividad 4):
            totales, agrupaciones, rankings, árbol por pérdida y grafo
            menú-ingrediente. Python puro (sin Streamlit ni Supabase).
 Librerías: ninguna externa
==========================================================================

Recibe los registros tal como los entrega datos/base_datos.py (listas de
diccionarios) y devuelve resultados listos para mostrar.
"""
from __future__ import annotations

from logica.estructuras import ArbolBinarioBusqueda, Grafo, mayores
from logica.ordenamiento import merge_sort


def indicadores(ordenes: list[dict]) -> dict:
    """KPIs globales del panel. Las órdenes anuladas ya vienen excluidas."""
    costo = sum(o["costo_total"] for o in ordenes)
    perdida = sum(o["perdida_merma"] for o in ordenes)
    ingresos = sum(o["venta_total"] for o in ordenes)
    return {
        "servicios": len(ordenes),
        "comensales": sum(o["comensales"] for o in ordenes),
        "costo_total": costo,
        "perdida_total": perdida,
        "ingresos": ingresos,
        "ganancia": ingresos - costo,
        "porcentaje_merma": perdida / costo if costo else 0.0,
    }


def totales_por(filas: list[dict], grupo: str, sumas: tuple[str, ...]) -> list[dict]:
    """Agrupa las filas por el campo `grupo` sumando los campos `sumas`.
    Usa un diccionario (tabla hash, O(1) por fila) y luego ordena los grupos
    con merge_sort de mayor a menor según el primer campo de `sumas`."""
    grupos = {}
    for fila in filas:
        clave = fila[grupo]
        if clave not in grupos:
            grupos[clave] = {grupo: clave, "registros": 0, **{campo: 0 for campo in sumas}}
        acumulado = grupos[clave]
        acumulado["registros"] += 1
        for campo in sumas:
            acumulado[campo] += fila[campo]
    return merge_sort(list(grupos.values()), clave=lambda g: g[sumas[0]], descendente=True)


def mayores_perdidas(ordenes: list[dict], cantidad: int = 5) -> list[dict]:
    """Las `cantidad` órdenes con mayor pérdida, con la cola con prioridad."""
    return mayores(ordenes, clave=lambda o: o["perdida_merma"], cantidad=cantidad)


def arbol_por_perdida(ordenes: list[dict]) -> ArbolBinarioBusqueda:
    """Árbol binario de búsqueda con la pérdida de cada orden como clave."""
    arbol = ArbolBinarioBusqueda()
    for orden in ordenes:
        arbol.insertar(orden["perdida_merma"], orden)
    return arbol


def grafo_menu_ingrediente(recetas, detalle: list[dict] | None = None) -> Grafo:
    """Grafo bipartito: una arista menú-ingrediente por cada ingrediente de
    cada receta. Si se entrega el detalle de las órdenes, el peso de cada
    arista acumula la pérdida por merma de ese ingrediente en ese menú."""
    grafo = Grafo()
    for receta in recetas:
        grafo.agregar_vertice(receta.nombre, "menu")
        for ingrediente in receta.ingredientes():
            grafo.agregar_vertice(ingrediente.nombre, "ingrediente")
            grafo.agregar_arista(receta.nombre, ingrediente.nombre, 0.0)
    for fila in detalle or []:
        if grafo.existe_arista(fila["menu"], fila["ingrediente"]):
            grafo.sumar_peso(fila["menu"], fila["ingrediente"], fila["perdida_merma"])
    return grafo


def menus_relacionados(grafo: Grafo, menu: str) -> list[str]:
    """Menús que comparten al menos un ingrediente con `menu`: en el grafo
    bipartito están a 2 saltos (menú -> ingrediente -> menú)."""
    return sorted(vertice for vertice, distancia in grafo.recorrido_anchura(menu, max_saltos=2)
                  if distancia == 2 and grafo.tipo(vertice) == "menu")


def pares_con_mas_perdida(grafo: Grafo, cantidad: int = 5) -> list[dict]:
    """Ranking de los pares menú-ingrediente que más pierden (cola con prioridad)."""
    pares = [{"menu": menu, "ingrediente": ingrediente, "perdida": grafo.peso(menu, ingrediente)}
             for menu in grafo.vertices("menu") for ingrediente in grafo.vecinos(menu)]
    return [par for par in mayores(pares, clave=lambda p: p["perdida"], cantidad=cantidad) if par["perdida"] > 0]
