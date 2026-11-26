"""
==========================================================================
 Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
 Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
--------------------------------------------------------------------------
 Archivo  : logica/modelos.py
 Propósito: Clases (TDA) que modelan ingredientes, recetas y órdenes.
 Librerías: dataclasses, fractions (biblioteca estándar de Python)
==========================================================================

Decisión: se usan @dataclass porque cada clase es principalmente un conjunto
de datos con nombre; dataclass genera __init__, __repr__ y __eq__ y deja el
código corto y legible. Los montos se guardan como Fraction (fracción exacta)
para que la merma y el costo por plato no arrastren errores de redondeo de
los float (por ejemplo, 1/3 de kg); se redondean solo al mostrar o guardar.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction


@dataclass(frozen=True)
class Ingrediente:
    """Insumo de la tabla del enunciado.

    Un *envase* es la unidad de compra indivisible: 1 cebolla, 1 paquete,
    1 kg, 1 empaque o 1 litro. `rendimiento` es la columna "Utilidad":
    cuántas personas alcanza un envase.
    frozen=True lo hace inmutable: nadie puede cambiar un costo a mitad de
    un cálculo.
    """
    id: int
    nombre: str
    costo_envase: int                       # $ por envase
    unidad_compra: str                      # 'unidad', 'paquete', 'kg', 'empaque' o 'litro'
    rendimiento: int                        # personas (porciones) por envase
    unidades_por_envase: int | None = None  # equivalencia para cocina, ej. 4 papas por kg
    nombre_unidad: str | None = None        # 'papas', 'tomates', 'huevos', 'ml'
    supuesto: str | None = None             # aclaración documentada

    @property
    def costo_porcion(self) -> Fraction:
        """Lo que cuesta la parte de una persona: costo del envase / personas que rinde."""
        return Fraction(self.costo_envase, self.rendimiento)


@dataclass(frozen=True)
class LineaReceta:
    """Un ingrediente dentro de una receta, con la cantidad que indica el
    enunciado para `comensales_base` personas. Se guarda como referencia: el
    cálculo usa el rendimiento de la tabla (ver logica/calculo.py)."""
    ingrediente: Ingrediente
    cantidad_base: float
    unidad_receta: str                      # 'unidades' o 'porciones'


@dataclass
class Receta:
    """Menú: su nombre y la LISTA de sus ingredientes (TDA lista)."""
    id: int
    nombre: str
    comensales_base: int = 4
    lineas: list[LineaReceta] = field(default_factory=list)
    observacion: str | None = None

    def ingredientes(self) -> list[Ingrediente]:
        return [linea.ingrediente for linea in self.lineas]


@dataclass(frozen=True)
class DetalleInsumo:
    """Resultado del cálculo para UN ingrediente de una orden."""
    ingrediente: Ingrediente
    porciones_requeridas: int      # una porción por comensal
    envases: int                   # unidades completas a abrir (redondeo hacia arriba)
    porciones_compradas: int       # envases x rendimiento
    porciones_sobrantes: int       # compradas - requeridas
    cantidad_requerida: Fraction   # en unidad de compra (ej. 5/2 kg)
    merma_fisica: Fraction         # en unidad de compra (ej. 1/2 kg)
    costo: int                     # $ de los envases abiertos
    perdida: Fraction              # $ de la merma


@dataclass
class Orden:
    """Servicio solicitado por cocina: menú, comensales y todo lo calculado.

    Los totales los llena logica/calculo.py. id, usuario y estado se completan
    al guardar la orden en la base de datos.
    """
    receta: Receta
    comensales: int
    detalles: list[DetalleInsumo]
    costo_total: int
    perdida_total: Fraction
    costo_por_plato: Fraction
    precio_venta_plato: Fraction
    venta_total: Fraction
    id: int | None = None
    usuario: str | None = None
    estado: str = "pendiente"

    @property
    def costo_aprovechado(self) -> Fraction:
        """Parte del costo que sí terminó en los platos (costo total - merma)."""
        return self.costo_total - self.perdida_total
