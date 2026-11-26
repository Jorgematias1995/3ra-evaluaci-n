# ==========================================================================
#  Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
#  Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
#  Archivo: __init__.py del paquete (convierte la carpeta en paquete de Python)
#  Librerías: ninguna
# ==========================================================================
"""
Capa de LÓGICA (Python puro: no usa Streamlit ni Supabase).

  modelos.py       Clases del dominio: Ingrediente, LineaReceta, Receta, DetalleInsumo, Orden
  estructuras.py   TDA: Pila, Cola, ColaPrioridad (montículo), ArbolBinarioBusqueda, Grafo
  ordenamiento.py  Inserción, merge sort, ordenamiento externo y búsqueda secuencial
  calculo.py       Motor de cálculo: envases (math.ceil), merma, costo por plato y venta
  analisis.py      Indicadores, agrupaciones y rankings para el administrador
  supuestos.py     Supuestos y decisiones del cálculo (se muestran en la app)

Al no depender de la interfaz ni de la base de datos, esta capa se prueba sola
(tests/test_logica.py) y se puede reutilizar con otra interfaz.
"""
