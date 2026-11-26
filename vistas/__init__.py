# ==========================================================================
#  Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
#  Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
#  Archivo: __init__.py del paquete (convierte la carpeta en paquete de Python)
#  Librerías: ninguna
# ==========================================================================
"""
Capa de INTERFAZ (Streamlit). Cada archivo es una página:

  ingreso.py   Formulario de usuario y contraseña
  cocina.py    Perfil cocina: solicitud de servicio, orden de preparación,
               cola de preparación, historial de la sesión y consulta de insumos
  panel.py     Administrador: indicadores (KPIs) y gráficos principales
  historial.py Administrador: historial filtrable, detalle y exportación
  mermas.py    Administrador: análisis de desechos e impacto económico
  catalogo.py  Administrador: ingredientes, recetas y supuestos del cálculo
  graficos.py  Gráficos (Altair) con un mismo estilo
  encabezado.py Título de página con la imagen del local (carpeta assets/)
  formato.py   Formato chileno de montos, cantidades y fechas

Las vistas no calculan ni consultan tablas: le piden el cálculo a
logica/calculo.py y los datos a datos/base_datos.py.
"""

# Nombre del local, en un solo lugar (título, pestaña del navegador y menú lateral).
NOMBRE_LOCAL = "Noches alegres, mañanas tristes"
