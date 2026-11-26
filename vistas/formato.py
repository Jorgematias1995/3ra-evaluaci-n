"""
==========================================================================
 Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
 Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
--------------------------------------------------------------------------
 Archivo  : vistas/formato.py
 Propósito: Mostrar montos, cantidades y fechas en formato chileno
            ($11.000 · 2,5 kg · 26-11-2026 14:05).
 Librerías: pandas (fechas), fractions (estándar)
==========================================================================
"""
from __future__ import annotations

from fractions import Fraction

import pandas as pd

ZONA_HORARIA = "America/Santiago"   # en Windows necesita el paquete tzdata (requirements.txt)
PLURAL = {"unidad": "unidades", "paquete": "paquetes", "kg": "kg", "empaque": "empaques", "litro": "litros"}


def _chileno(valor: float, decimales: int) -> str:
    """Formato inglés '1,234.50' -> chileno '1.234,50'."""
    entero, _, decimal = f"{valor:,.{decimales}f}".partition(".")
    entero = entero.replace(",", ".")
    return f"{entero},{decimal}" if decimal else entero


def numero(valor, decimales: int = 2) -> str:
    """Cantidades: 1234.5 -> '1.234,5' (sin ceros de más)."""
    texto = _chileno(float(valor), decimales)
    return texto.rstrip("0").rstrip(",") if "," in texto else texto


def pesos(valor) -> str:
    """Montos: $11.000 o $1.466,67 (centavos solo si el monto los tiene)."""
    redondeado = round(float(valor), 2)
    return "$" + _chileno(redondeado, 0 if redondeado == round(redondeado) else 2)


def tabla_chilena(tabla: pd.DataFrame, montos=(), porcentajes=()):
    """Muestra montos como $1.234 y porcentajes como 5,2 % SIN convertirlos en
    texto (Styler de pandas): al ordenar con un clic en el encabezado de la
    tabla, se siguen ordenando como números y no como palabras."""
    formatos = {c: pesos for c in montos if c in tabla.columns}
    formatos.update({c: (lambda v: f"{numero(v, 1)} %") for c in porcentajes if c in tabla.columns})
    return tabla.style.format(formatos, na_rep="—")


def unidad(ingrediente, cantidad) -> str:
    """Unidad de compra en singular (cantidad 1) o plural."""
    return ingrediente.unidad_compra if cantidad == 1 else PLURAL.get(ingrediente.unidad_compra, ingrediente.unidad_compra)


def envases(ingrediente, cantidad: int) -> str:
    """Envases completos a retirar de bodega: '3 kg', '1 paquete', '5 unidades'."""
    return f"{cantidad} {unidad(ingrediente, cantidad)}"


def cantidad_fisica(ingrediente, cantidad: Fraction, porciones: int) -> str:
    """Cantidad expresada para cocina, con la equivalencia supuesta cuando existe:
    '2,5 kg (≈ 10 papas)', '10 huevos (0,83 empaques)', '7 porciones (0,7 paquetes)',
    '0,7 litros (700 ml)', '3,5 unidades'."""
    texto = f"{numero(cantidad)} {unidad(ingrediente, cantidad)}"
    if ingrediente.unidades_por_envase:
        equivalente = f"{numero(cantidad * ingrediente.unidades_por_envase)} {ingrediente.nombre_unidad}"
        if ingrediente.unidad_compra == "empaque":           # los huevos se cuentan de a uno
            return f"{equivalente} ({texto})"
        aproximado = "" if ingrediente.nombre_unidad == "ml" else "≈ "   # ml es exacto; papas y tomates, supuesto
        return f"{texto} ({aproximado}{equivalente})"
    if ingrediente.unidad_compra == "paquete":
        return f"{porciones} porciones ({texto})"
    return texto


def fecha_local(valor) -> str:
    """Fecha ISO guardada en UTC por Supabase -> hora de Chile '26-11-2026 14:05'."""
    if not valor:
        return ""
    instante = pd.Timestamp(valor)
    if instante.tzinfo is None:                 # sin zona: se asume UTC (así guarda Supabase)
        instante = instante.tz_localize("UTC")
    return instante.tz_convert(ZONA_HORARIA).strftime("%d-%m-%Y %H:%M")


def hora_actual() -> str:
    """Hora de Chile en este momento, '14:05'."""
    return pd.Timestamp.now(tz=ZONA_HORARIA).strftime("%H:%M")
