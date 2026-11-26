"""
==========================================================================
 Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
 Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
--------------------------------------------------------------------------
 Archivo  : logica/ordenamiento.py
 Propósito: Algoritmos de ordenamiento (interno y externo) y de búsqueda
            secuencial usados para organizar, filtrar y jerarquizar las
            preparaciones y las pérdidas por merma.
 Librerías: json, os, tempfile, unicodedata, dataclasses (estándar)
==========================================================================

Algoritmos y su uso en el sistema:

  ordenamiento_insercion  O(n²). Ingredientes de UNA orden (4 o 5 elementos)
                          por nombre: con listas tan cortas es el más simple
                          y rápido, y es estable.
  merge_sort              O(n log n) siempre y estable. Historial completo de
                          órdenes por la columna que elija el administrador.
  ordenamiento_externo    Mezcla de corridas en disco: ordena el historial por
                          bloques que "caben en memoria" y luego los mezcla con
                          una cola con prioridad. Exportación del historial.
  busqueda_secuencial     O(n). Validar el usuario al ingresar y consultar
                          insumos por nombre (no requiere lista ordenada).

"Estable" significa que dos registros con la misma clave conservan su orden
original (por ejemplo, dos órdenes con igual pérdida siguen por fecha).
"""
from __future__ import annotations

import json
import os
import tempfile
import unicodedata
from dataclasses import dataclass

from logica.estructuras import ColaPrioridad


def _va_despues(a, b, descendente: bool) -> bool:
    """True si la clave a debe ir DESPUÉS que la clave b. Es estricta (>, <):
    con claves iguales devuelve False y los elementos no se intercambian,
    eso es lo que hace estables a los algoritmos."""
    return a < b if descendente else a > b


# ==========================================================================
# ORDENAMIENTO INTERNO (todo en memoria)
# ==========================================================================
def ordenamiento_insercion(lista, clave=lambda x: x, descendente: bool = False) -> list:
    """Inserción: toma cada elemento y lo corre hacia la izquierda hasta su
    lugar dentro de la parte ya ordenada. Devuelve una lista nueva."""
    resultado = list(lista)
    for i in range(1, len(resultado)):
        actual = resultado[i]
        j = i - 1
        while j >= 0 and _va_despues(clave(resultado[j]), clave(actual), descendente):
            resultado[j + 1] = resultado[j]     # corre el mayor una posición a la derecha
            j -= 1
        resultado[j + 1] = actual
    return resultado


def merge_sort(lista, clave=lambda x: x, descendente: bool = False) -> list:
    """Merge sort (divide y vencerás): parte la lista en dos mitades, ordena
    cada una (recursivamente) y las mezcla. La recursión tiene profundidad
    log2(n): con 1.000.000 de registros son solo 20 niveles."""
    if len(lista) <= 1:
        return list(lista)
    medio = len(lista) // 2
    izquierda = merge_sort(lista[:medio], clave, descendente)
    derecha = merge_sort(lista[medio:], clave, descendente)
    return _mezclar(izquierda, derecha, clave, descendente)


def _mezclar(izquierda, derecha, clave, descendente) -> list:
    """Une dos listas ya ordenadas comparando sus primeros elementos."""
    resultado = []
    i = j = 0
    while i < len(izquierda) and j < len(derecha):
        if _va_despues(clave(izquierda[i]), clave(derecha[j]), descendente):
            resultado.append(derecha[j])
            j += 1
        else:                       # con empate gana la izquierda: estable
            resultado.append(izquierda[i])
            i += 1
    resultado.extend(izquierda[i:])     # lo que quede ya está ordenado
    resultado.extend(derecha[j:])
    return resultado


# ==========================================================================
# ORDENAMIENTO EXTERNO (mezcla de corridas en disco)
# ==========================================================================
@dataclass
class ResultadoExterno:
    registros: list         # registros ordenados
    corridas: int           # cuántos archivos temporales se generaron
    tam_bloque: int         # registros por corrida (lo que "cabe en memoria")


def ordenamiento_externo(registros, campo: str, tam_bloque: int = 50,
                         descendente: bool = False) -> ResultadoExterno:
    """Ordenamiento externo por mezcla (external merge sort).

    Se usa cuando los datos no caben en memoria; aquí se simula con un
    tamaño de bloque pequeño para que el proceso sea visible:

      1) División: se leen los registros de a `tam_bloque`; cada bloque se
         ordena en memoria (merge_sort) y se escribe a disco como una
         "corrida" (un archivo .jsonl con un registro por línea).
      2) Mezcla de k vías: se abren todas las corridas y se lee UNA línea de
         cada una. Una ColaPrioridad dice cuál de esas k cabezas va primero;
         se saca, se agrega a la salida y se lee la siguiente línea de la
         misma corrida. En memoria nunca hay más de k registros a la vez.

    Los registros deben ser diccionarios serializables a JSON y `campo` la
    clave por la que se ordena.
    """
    if tam_bloque < 1:
        raise ValueError("El tamaño de bloque debe ser al menos 1")
    with tempfile.TemporaryDirectory(prefix="orden_externo_") as carpeta:
        # -- Fase 1: corridas ordenadas en disco ------------------------------
        rutas = []
        bloque = []
        for registro in registros:
            bloque.append(registro)
            if len(bloque) == tam_bloque:
                rutas.append(_escribir_corrida(carpeta, len(rutas), bloque, campo, descendente))
                bloque = []
        if bloque:
            rutas.append(_escribir_corrida(carpeta, len(rutas), bloque, campo, descendente))

        # -- Fase 2: mezcla de k vías con cola con prioridad -------------------
        archivos = [open(ruta, encoding="utf-8") for ruta in rutas]
        try:
            cola = ColaPrioridad(mayor_primero=descendente)
            for numero, archivo in enumerate(archivos):
                _leer_siguiente(archivo, numero, campo, cola)
            salida = []
            while not cola.esta_vacia():
                numero, registro = cola.extraer()
                salida.append(registro)
                _leer_siguiente(archivos[numero], numero, campo, cola)
        finally:
            for archivo in archivos:
                archivo.close()
    # Aquí la salida se junta en una lista porque luego se muestra y se
    # descarga; con millones de registros se escribiría directo a un archivo.
    return ResultadoExterno(registros=salida, corridas=len(rutas), tam_bloque=tam_bloque)


def _escribir_corrida(carpeta, numero, bloque, campo, descendente) -> str:
    ruta = os.path.join(carpeta, f"corrida_{numero:03d}.jsonl")
    ordenado = merge_sort(bloque, clave=lambda r: r[campo], descendente=descendente)
    with open(ruta, "w", encoding="utf-8") as archivo:
        for registro in ordenado:
            archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return ruta


def _leer_siguiente(archivo, numero, campo, cola) -> None:
    """Lee la próxima línea de una corrida y la pone en la cola. El desempate
    por número de corrida mantiene el algoritmo estable: con claves iguales
    sale primero el registro de la corrida anterior (que venía antes)."""
    linea = archivo.readline()
    if linea:
        registro = json.loads(linea)
        cola.insertar((numero, registro), registro[campo], desempate=numero)


# ==========================================================================
# BÚSQUEDA SECUENCIAL
# ==========================================================================
def busqueda_secuencial(lista, criterio):
    """Recorre la lista desde el inicio y se detiene en el PRIMER elemento que
    cumple `criterio`. O(n), no necesita que la lista esté ordenada.
    Devuelve (elemento o None, comparaciones realizadas)."""
    comparaciones = 0
    for elemento in lista:
        comparaciones += 1
        if criterio(elemento):
            return elemento, comparaciones
    return None, comparaciones


def busqueda_secuencial_todos(lista, criterio) -> list:
    """Variante que recorre la lista completa y devuelve TODOS los que cumplen
    (ej. todos los insumos cuyo nombre contiene "pa": papa y ...)."""
    return [elemento for elemento in lista if criterio(elemento)]


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para que 'cebolla', 'Cebolla' y 'CEBOLLÁ'
    coincidan en la búsqueda."""
    sin_tildes = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in sin_tildes if not unicodedata.combining(c)).lower().strip()
