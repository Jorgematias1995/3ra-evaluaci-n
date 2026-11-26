"""
==========================================================================
 Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
 Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
--------------------------------------------------------------------------
 Archivo  : logica/calculo.py
 Propósito: Motor de cálculo (Actividad 2): envases indivisibles, merma
            física, pérdida por merma, costo por plato y precio de venta.
 Librerías: math, fractions (biblioteca estándar de Python)
==========================================================================

REGLA DE CÁLCULO (decisión documentada)
El enunciado entrega dos fuentes que no calzan entre sí: la tabla de
ingredientes ("Utilidad": personas por envase) y las recetas (cantidades para
4 comensales). Ej.: la tabla dice 1 lechuga cada 10 personas y las recetas
usan 1 lechuga para 4. Se decidió calcular con la TABLA, porque el enunciado
pide "con la información de la tabla adjunta" y habla de "utilidad/rendimiento
por comensal". La receta define QUÉ insumos lleva cada menú; sus cantidades
quedan guardadas como referencia.

Para cada insumo del menú y N comensales (1 porción por comensal):
  envases             = ceil(N / rendimiento)          productos indivisibles
  porciones_sobrantes = envases * rendimiento - N      no se pueden guardar
  merma física        = porciones_sobrantes / rendimiento   (en kg, paquetes...)
  pérdida por merma   = merma física * costo del envase

Para la orden completa:
  costo total        = suma de envases * costo de cada insumo
  costo por plato    = costo total / N   (costo REAL: incluye lo que se bota)
  precio de venta    = costo por plato * 1,25   (25 % de ganancia sobre el costo)

Ejemplo (Tortilla de Papas y Cebolla, 10 comensales):
  Papa    ceil(10/4)  = 3 kg       $3.000   sobra 0,5 kg       pierde $500
  Cebolla ceil(10/4)  = 3 unid.    $1.500   sobra 0,5 cebolla  pierde $250
  Huevo   ceil(10/12) = 1 empaque  $4.500   sobra 2/12         pierde $750
  Aceite  ceil(10/10) = 1 litro    $1.000   sobra 0            pierde $0
  Total $10.000 -> $1.000 por plato -> venta $1.250 por plato
"""
from __future__ import annotations

import math
from fractions import Fraction

from logica.modelos import DetalleInsumo, Ingrediente, Orden, Receta

# Margen de ganancia: 25 % SOBRE el costo real por plato (precio = costo x 1,25).
MARGEN_GANANCIA = Fraction(25, 100)

# Supuesto: capacidad máxima de un servicio. Evita errores de tipeo (ej. 5000
# en vez de 50); el CHECK de la tabla ordenes tiene el mismo límite.
MAX_COMENSALES = 1000


class ErrorValidacion(ValueError):
    """Dato de entrada inválido: la interfaz muestra el mensaje al usuario."""


def validar_comensales(valor) -> int:
    """Devuelve la cantidad de comensales como entero o lanza ErrorValidacion.
    Rechaza: vacío (None), texto, decimales, cero, negativos y más del máximo."""
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        raise ErrorValidacion("Ingrese la cantidad de comensales.")
    if isinstance(valor, bool):                # True/False no son cantidades
        raise ErrorValidacion("La cantidad de comensales debe ser un número entero.")
    try:
        numero = Fraction(str(valor).strip())  # acepta 25, "25", 25.0; rechaza "abc"
    except (ValueError, ZeroDivisionError):
        raise ErrorValidacion("La cantidad de comensales debe ser un número entero.") from None
    if numero.denominator != 1:
        raise ErrorValidacion("La cantidad de comensales debe ser un número entero (sin decimales).")
    if numero == 0:
        raise ErrorValidacion("La cantidad de comensales no puede ser cero.")
    if numero < 0:
        raise ErrorValidacion("La cantidad de comensales no puede ser negativa.")
    if numero > MAX_COMENSALES:
        raise ErrorValidacion(f"El máximo por servicio es {MAX_COMENSALES} comensales.")
    return int(numero)


def calcular_insumo(ingrediente: Ingrediente, comensales: int) -> DetalleInsumo:
    """Cálculo de UN ingrediente para `comensales` personas."""
    porciones_requeridas = comensales                          # 1 porción por comensal

    # Indivisibilidad: si 1 kg de papa alcanza para 4 personas, 10 personas
    # necesitan 2,5 kg, pero no se vende medio kilo: se abren 3 (math.ceil).
    # Se divide con Fraction (exacta) para que ceil no falle por un decimal
    # mal representado en float.
    envases = math.ceil(Fraction(porciones_requeridas, ingrediente.rendimiento))

    # No se puede guardar lo abierto: todo lo que sobra es merma.
    porciones_compradas = envases * ingrediente.rendimiento
    porciones_sobrantes = porciones_compradas - porciones_requeridas

    # Cantidades en la unidad de compra (kg, paquetes, empaques, litros...).
    cantidad_requerida = Fraction(porciones_requeridas, ingrediente.rendimiento)
    merma_fisica = Fraction(porciones_sobrantes, ingrediente.rendimiento)

    costo = envases * ingrediente.costo_envase                 # se paga el envase completo
    perdida = merma_fisica * ingrediente.costo_envase          # $ de la parte que se bota

    return DetalleInsumo(
        ingrediente=ingrediente,
        porciones_requeridas=porciones_requeridas,
        envases=envases,
        porciones_compradas=porciones_compradas,
        porciones_sobrantes=porciones_sobrantes,
        cantidad_requerida=cantidad_requerida,
        merma_fisica=merma_fisica,
        costo=costo,
        perdida=perdida,
    )


def calcular_orden(receta: Receta, comensales) -> Orden:
    """Calcula la orden completa de un menú. Lanza ErrorValidacion si los
    comensales no son válidos o si la receta no tiene ingredientes."""
    comensales = validar_comensales(comensales)
    if not receta.lineas:
        raise ErrorValidacion(f"La receta «{receta.nombre}» no tiene ingredientes registrados.")

    detalles = [calcular_insumo(linea.ingrediente, comensales) for linea in receta.lineas]

    costo_total = sum(detalle.costo for detalle in detalles)
    perdida_total = sum((detalle.perdida for detalle in detalles), Fraction(0))

    # Costo REAL por plato: el costo de TODO lo abierto (incluida la merma)
    # repartido entre los comensales. Esa es la base del margen del 25 %.
    costo_por_plato = Fraction(costo_total, comensales)
    precio_venta_plato = costo_por_plato * (1 + MARGEN_GANANCIA)
    venta_total = precio_venta_plato * comensales

    return Orden(
        receta=receta,
        comensales=comensales,
        detalles=detalles,
        costo_total=costo_total,
        perdida_total=perdida_total,
        costo_por_plato=costo_por_plato,
        precio_venta_plato=precio_venta_plato,
        venta_total=venta_total,
    )


def a_pesos(valor: Fraction) -> float:
    """Redondea un monto exacto a 2 decimales (mitad hacia arriba) para
    guardarlo en la base de datos (columnas numeric(12,2))."""
    centavos = math.floor(Fraction(valor) * 100 + Fraction(1, 2))
    return centavos / 100


# ==========================================================================
# Apoyo a decisiones logísticas (vista de análisis de mermas)
# ==========================================================================
def comensales_sin_merma(receta: Receta) -> int:
    """Menor cantidad de comensales con merma cero: el mínimo común múltiplo
    de los rendimientos (ej. tortilla: mcm(4, 4, 12, 10) = 60)."""
    return math.lcm(*(linea.ingrediente.rendimiento for linea in receta.lineas))


def simular_comensales(receta: Receta, desde: int = 1, hasta: int = 60) -> list[dict]:
    """Calcula la orden para cada cantidad de comensales del rango, sin
    guardar nada: muestra cómo cambia la merma según el tamaño del grupo."""
    filas = []
    for n in range(desde, hasta + 1):
        orden = calcular_orden(receta, n)
        filas.append({
            "comensales": n,
            "perdida_total": float(orden.perdida_total),
            "perdida_por_plato": float(orden.perdida_total / n),
            "costo_por_plato": float(orden.costo_por_plato),
        })
    return filas
