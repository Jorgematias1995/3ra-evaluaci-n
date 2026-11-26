"""
==========================================================================
 Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
 Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
--------------------------------------------------------------------------
 Archivo  : datos/base_datos.py
 Propósito: Capa de datos. Lee el catálogo (ingredientes y recetas), guarda
            cada orden con su detalle y entrega el historial al panel.
 Librerías: streamlit (secrets y caché), supabase (cliente oficial),
            datetime (estándar)
==========================================================================

Seguridad: la URL y la secret key se leen de st.secrets, que Streamlit carga
desde .streamlit/secrets.toml (archivo local excluido del repositorio por
.gitignore) o desde los Secrets de Streamlit Cloud. En el código no hay
ninguna clave.

Caché: el catálogo casi no cambia (5 minutos); el historial se guarda 15
segundos y se limpia apenas se registra o modifica una orden, para que el
panel del administrador vea los datos nuevos al tiro.
"""
from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st
from supabase import create_client

from logica.calculo import a_pesos
from logica.modelos import Ingrediente, LineaReceta, Orden, Receta

TAMANO_PAGINA = 1000   # Supabase entrega como máximo 1.000 filas por consulta
CAMPOS_DECIMALES = ("costo_por_plato", "precio_venta_plato", "venta_total", "perdida_merma", "merma_fisica")


@st.cache_resource(show_spinner=False)
def cliente():
    """Un solo cliente de Supabase para toda la aplicación (cache_resource)."""
    config = st.secrets["supabase"]
    return create_client(config["url"], config["key"])


def _todas_las_filas(armar_consulta) -> list[dict]:
    """Pide los resultados en páginas de 1.000 filas hasta traerlos todos."""
    filas, inicio = [], 0
    while True:
        lote = armar_consulta().range(inicio, inicio + TAMANO_PAGINA - 1).execute().data
        filas.extend(lote)
        if len(lote) < TAMANO_PAGINA:
            return filas
        inicio += TAMANO_PAGINA


def _a_float(fila: dict) -> dict:
    """PostgREST puede entregar los numeric como texto o número: se unifican a float."""
    for campo in CAMPOS_DECIMALES:
        if fila.get(campo) is not None:
            fila[campo] = float(fila[campo])
    return fila


def limpiar_cache() -> None:
    _ordenes.clear()
    _detalle.clear()


# ==========================================================================
# Usuarios
# ==========================================================================
def usuarios() -> list[dict]:
    """Usuarios con los permisos de su rol (JOIN usuarios -> roles por la llave
    foránea). Sin caché: si se desactiva un usuario, deja de entrar de inmediato."""
    return (cliente().table("usuarios")
            .select("usuario, nombre, rol, clave_hash, activo, roles(ve_costos, ve_panel)")
            .order("id").execute().data)


# ==========================================================================
# Catálogo: ingredientes y recetas
# ==========================================================================
@st.cache_data(ttl=300, show_spinner=False)
def _catalogo() -> tuple[list[dict], list[dict]]:
    ingredientes = cliente().table("ingredientes").select("*").order("id").execute().data
    # JOIN recetas -> receta_ingredientes en una sola consulta (PostgREST
    # sigue la llave foránea receta_ingredientes.receta_id).
    recetas = (cliente().table("recetas")
               .select("id, nombre, comensales_base, observacion, "
                       "receta_ingredientes(ingrediente_id, cantidad_base, unidad_receta)")
               .order("id").execute().data)
    return ingredientes, recetas


def _a_ingrediente(fila: dict) -> Ingrediente:
    return Ingrediente(
        id=fila["id"],
        nombre=fila["nombre"],
        costo_envase=int(fila["costo_envase"]),
        unidad_compra=fila["unidad_compra"],
        rendimiento=int(fila["rendimiento_personas"]),
        unidades_por_envase=fila.get("unidades_por_envase"),
        nombre_unidad=fila.get("nombre_unidad"),
        supuesto=fila.get("supuesto"),
    )


def ingredientes() -> list[Ingrediente]:
    filas, _ = _catalogo()
    return [_a_ingrediente(fila) for fila in filas]


def recetas() -> list[Receta]:
    """Recetas como objetos Receta, cada una con su lista de LineaReceta."""
    filas_ingredientes, filas_recetas = _catalogo()
    # Diccionario id -> Ingrediente: encontrar el ingrediente de cada línea en O(1).
    por_id = {fila["id"]: _a_ingrediente(fila) for fila in filas_ingredientes}
    lista = []
    for fila in filas_recetas:
        lineas = [LineaReceta(por_id[l["ingrediente_id"]], float(l["cantidad_base"]), l["unidad_receta"])
                  for l in fila.get("receta_ingredientes") or []]
        lista.append(Receta(fila["id"], fila["nombre"], fila["comensales_base"], lineas, fila.get("observacion")))
    return lista


# ==========================================================================
# Órdenes (servicios) y su detalle
# ==========================================================================
def guardar_orden(orden: Orden, usuario: str) -> int:
    """Guarda la orden y su detalle por insumo. Devuelve el id asignado."""
    fila = {
        "receta_id": orden.receta.id,
        "usuario": usuario,
        "comensales": orden.comensales,
        "costo_total": orden.costo_total,
        "costo_por_plato": a_pesos(orden.costo_por_plato),
        "precio_venta_plato": a_pesos(orden.precio_venta_plato),
        "venta_total": a_pesos(orden.venta_total),
        "perdida_merma": a_pesos(orden.perdida_total),
        "estado": "pendiente",
    }
    creada = cliente().table("ordenes").insert(fila).execute().data[0]
    detalle = [{
        "orden_id": creada["id"],
        "ingrediente_id": d.ingrediente.id,
        "porciones_requeridas": d.porciones_requeridas,
        "envases": d.envases,
        "porciones_sobrantes": d.porciones_sobrantes,
        "merma_fisica": round(float(d.merma_fisica), 4),
        "costo": d.costo,
        "perdida_merma": a_pesos(d.perdida),
    } for d in orden.detalles]
    try:
        cliente().table("orden_detalle").insert(detalle).execute()   # todas las filas en una llamada
    except Exception:
        # La API no permite una transacción entre dos inserciones: si el
        # detalle falla, se borra la orden para no dejar un registro a medias.
        cliente().table("ordenes").delete().eq("id", creada["id"]).execute()
        raise
    limpiar_cache()
    orden.id, orden.usuario = creada["id"], usuario
    return creada["id"]


@st.cache_data(ttl=15, show_spinner=False)
def _ordenes() -> list[dict]:
    # JOIN ordenes -> recetas para traer el nombre del menú.
    return _todas_las_filas(lambda: cliente().table("ordenes").select("*, recetas(nombre)").order("id"))


@st.cache_data(ttl=15, show_spinner=False)
def _detalle() -> list[dict]:
    return _todas_las_filas(lambda: cliente().table("orden_detalle")
                            .select("*, ingredientes(nombre, unidad_compra)").order("id"))


def ordenes(incluir_anuladas: bool = False) -> list[dict]:
    """Historial de órdenes, con el nombre del menú en la clave 'menu'.
    Las anuladas (deshechas por cocina) no cuentan en los indicadores."""
    resultado = []
    for fila in _ordenes():
        if fila["estado"] == "anulada" and not incluir_anuladas:
            continue
        orden = _a_float(dict(fila))
        orden["menu"] = (orden.pop("recetas", None) or {}).get("nombre", "(sin menú)")
        resultado.append(orden)
    return resultado


def detalle_ordenes(incluir_anuladas: bool = False) -> list[dict]:
    """Detalle por insumo de todas las órdenes, con el menú y el estado de su orden."""
    ordenes_por_id = {o["id"]: o for o in ordenes(incluir_anuladas=True)}
    resultado = []
    for fila in _detalle():
        orden = ordenes_por_id.get(fila["orden_id"])
        if orden is None or (orden["estado"] == "anulada" and not incluir_anuladas):
            continue
        detalle = _a_float(dict(fila))
        insumo = detalle.pop("ingredientes", None) or {}
        detalle.update(ingrediente=insumo.get("nombre", "?"), unidad_compra=insumo.get("unidad_compra", ""),
                       menu=orden["menu"], estado=orden["estado"], fecha=orden["fecha"])
        resultado.append(detalle)
    return resultado


def ordenes_pendientes() -> list[dict]:
    """Órdenes por preparar, de la más antigua a la más nueva (orden de
    llegada). Sin caché: la cola de cocina siempre debe estar al día."""
    filas = (cliente().table("ordenes")
             .select("id, fecha, comensales, usuario, estado, recetas(nombre)")
             .eq("estado", "pendiente").order("id").execute().data)
    for fila in filas:
        fila["menu"] = (fila.pop("recetas", None) or {}).get("nombre", "(sin menú)")
    return filas


def detalle_de_orden(orden_id: int) -> list[dict]:
    """Insumos de una orden (cantidades, sin montos) para la cola de cocina."""
    return (cliente().table("orden_detalle")
            .select("ingrediente_id, porciones_requeridas, envases")
            .eq("orden_id", orden_id).order("id").execute().data)


def cambiar_estado(orden_id: int, nuevo: str, solo_si: str = "pendiente") -> bool:
    """Cambia el estado de una orden solo si sigue en `solo_si` (una sola
    sentencia UPDATE ... WHERE id = ? AND estado = ?). Devuelve False si otra
    persona ya la había cambiado."""
    filas = (cliente().table("ordenes")
             .update({"estado": nuevo, "actualizado_en": datetime.now(timezone.utc).isoformat()})
             .eq("id", orden_id).eq("estado", solo_si).execute().data)
    limpiar_cache()
    return bool(filas)
