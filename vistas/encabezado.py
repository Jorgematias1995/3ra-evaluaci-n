"""
==========================================================================
 Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
 Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
--------------------------------------------------------------------------
 Archivo  : vistas/encabezado.py
 Propósito: Título de página con una imagen al lado, para darle la
            personalidad del local (gerencia en el panel, cocina en la
            orden de preparación).
 Librerías: streamlit, pathlib (estándar)
==========================================================================

Las imágenes van en la carpeta assets/ con el nombre de la página:
gerencia.jpg (o .png, .webp) y cocina.webp (o .png, .jpg). Si una imagen no
está, la página muestra solo el título: la app nunca falla por una imagen.
"""
from pathlib import Path

import streamlit as st

CARPETA_IMAGENES = Path(__file__).resolve().parent.parent / "assets"
EXTENSIONES = (".png", ".jpg", ".jpeg", ".webp")


def _buscar_imagen(nombre: str) -> Path | None:
    """Primer archivo de assets/ que empiece con `nombre` y sea una imagen.
    Acepta también 'gerencia.jpg.jpg', que Windows crea al renombrar con las
    extensiones ocultas."""
    if not CARPETA_IMAGENES.is_dir():
        return None
    for ruta in sorted(CARPETA_IMAGENES.glob(f"{nombre}*")):
        if ruta.suffix.lower() in EXTENSIONES:
            return ruta
    return None


def titulo(texto: str, imagen: str, ancho: int = 110) -> None:
    """Título de la página y, a su derecha, la imagen assets/<imagen>.*"""
    ruta = _buscar_imagen(imagen)
    if ruta is None:
        st.title(texto)
        return
    columna_titulo, columna_imagen = st.columns([5, 1], vertical_alignment="center")
    columna_titulo.title(texto)
    columna_imagen.image(str(ruta), width=ancho)
