"""
==========================================================================
 Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
 Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
--------------------------------------------------------------------------
 Archivo  : logica/supuestos.py
 Propósito: Supuestos y decisiones del cálculo, en un solo lugar. La vista
            "Catálogo y supuestos" los muestra tal cual; el README los repite.
==========================================================================
"""

SUPUESTOS = [
    "**Regla de cálculo: rendimiento de la tabla.** Cada comensal consume una porción de cada "
    "ingrediente del menú, y la columna «Utilidad» indica cuántas porciones (personas) rinde un "
    "envase. Las recetas definen qué ingredientes lleva cada menú; sus cantidades (base 4 "
    "comensales) quedan guardadas como referencia, porque no calzan con la tabla (ej. la tabla "
    "dice 1 lechuga cada 10 personas y las recetas usan 1 lechuga para 4).",
    "**Productos indivisibles:** se abren envases completos, redondeando hacia arriba "
    "(math.ceil). **No se pueden guardar:** todo lo que sobra de un envase abierto es merma; "
    "cada orden abre sus propios envases y no queda stock para la siguiente.",
    "**Costo real por plato** = costo de todos los envases abiertos (incluida la merma) dividido "
    "por los comensales. **Precio de venta** = costo real por plato × 1,25 (25 % de ganancia "
    "sobre el costo).",
    "**Papa:** 1 kg = 4 papas (1 papa por persona, igual que la tabla: 4 personas por kg). Las "
    "recetas indican 6 papas para 4 comensales; esa diferencia queda anotada.",
    "**Tomate:** 1 kg = 4 tomates. La tabla indica 6 personas por kg, así que cada persona "
    "recibe 2/3 de tomate. **Huevo:** 1 empaque = 12 huevos (1 huevo por persona). "
    "**Aceite:** 1 litro = 10 porciones de 100 ml.",
    "**Carne Molida con Papas y Arroz** no lleva arroz, aunque el nombre lo mencione: se usa "
    "la lista de ingredientes de la receta.",
    "**Tuto de pollo** (tabla) es el mismo insumo que «Pollo (trutro/pechuga)» (recetas), y "
    "**Fideos** el mismo que «Fideos (espagueti)».",
    "**Máximo 1.000 comensales por servicio**, para evitar errores de tipeo.",
    "Una orden **anulada** por cocina (deshacer) queda en el historial pero no cuenta en los "
    "indicadores.",
]
