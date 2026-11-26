"""
==========================================================================
 Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
 Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
--------------------------------------------------------------------------
 Archivo  : scripts/crear_usuarios.py
 Propósito: Crear (o cambiarles la contraseña a) los usuarios 'cocina' y
            'administrador' en la tabla usuarios de Supabase.
 Librerías: supabase, getpass, tomllib (estándar desde Python 3.11; en
            versiones anteriores se usa el paquete toml que instala Streamlit)
==========================================================================

Uso (desde la carpeta del proyecto, con el entorno virtual activado y
después de ejecutar sql/01_esquema.sql y sql/02_datos.sql):

    python scripts/crear_usuarios.py

Lee la URL y la secret key de .streamlit/secrets.toml, pide la contraseña de
cada usuario dos veces (no se ve al escribir) y guarda solo su hash.
Se puede volver a ejecutar para cambiar las contraseñas.
"""
import getpass
import os
import sys

try:
    import tomllib                          # Python 3.11 o superior

    def leer_toml(ruta):
        with open(ruta, "rb") as archivo:
            return tomllib.load(archivo)
except ModuleNotFoundError:                 # Python 3.10 o anterior
    import toml

    def leer_toml(ruta):
        return toml.load(ruta)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from supabase import create_client  # noqa: E402

from seguridad.claves import generar_hash  # noqa: E402

# (usuario, nombre a mostrar, rol)
USUARIOS = [
    ("cocina", "Personal de cocina", "cocina"),
    ("administrador", "Administración del local", "administrador"),
]
LARGO_MINIMO = 6


def pedir_clave(usuario: str) -> str:
    while True:
        clave = getpass.getpass(f"Contraseña para '{usuario}' (mínimo {LARGO_MINIMO} caracteres): ")
        if len(clave) < LARGO_MINIMO:
            print("  Es muy corta, intente de nuevo.")
            continue
        if getpass.getpass("Repítala: ") != clave:
            print("  No coinciden, intente de nuevo.")
            continue
        return clave


def main() -> None:
    ruta = os.path.join(RAIZ, ".streamlit", "secrets.toml")
    if not os.path.exists(ruta):
        sys.exit("No existe .streamlit/secrets.toml (copie secrets.toml.example y complete la URL y la key).")
    config = leer_toml(ruta)["supabase"]
    supabase = create_client(config["url"], config["key"])

    roles = {fila["nombre"] for fila in supabase.table("roles").select("nombre").execute().data}
    if not {"cocina", "administrador"} <= roles:
        sys.exit("Faltan los roles: ejecute primero sql/01_esquema.sql y sql/02_datos.sql en Supabase.")

    for usuario, nombre, rol in USUARIOS:
        clave = pedir_clave(usuario)
        supabase.table("usuarios").upsert(
            {"usuario": usuario, "nombre": nombre, "rol": rol,
             "clave_hash": generar_hash(clave), "activo": True},
            on_conflict="usuario",          # si ya existe, actualiza (no duplica)
        ).execute()
        print(f"  OK: '{usuario}' guardado con rol {rol}.\n")
    print("Listo. Ya puede ingresar con: streamlit run app.py")


if __name__ == "__main__":
    main()
