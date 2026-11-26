"""
==========================================================================
 Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
 Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
--------------------------------------------------------------------------
 Archivo  : tests/test_logica.py
 Propósito: Pruebas de la capa de lógica, sin conexión a Supabase.
            Ejecutar desde la carpeta del proyecto:  python tests/test_logica.py
            (también funciona con pytest).
 Librerías: math, random, fractions (estándar)
==========================================================================

El motor de cálculo se contrasta con un método distinto e independiente:
"abrir envases de a uno hasta que alcance", para todas las recetas y de 1 a
120 comensales. Las estructuras y los ordenamientos se comparan con sorted()
de Python sobre datos aleatorios (incluidos empates, para probar estabilidad).
"""
import math
import os
import random
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logica import calculo  # noqa: E402
from logica.calculo import ErrorValidacion  # noqa: E402
from logica.estructuras import (ArbolBinarioBusqueda, Cola, ColaPrioridad, Grafo,  # noqa: E402
                                Pila, mayores)
from logica.modelos import Ingrediente, LineaReceta, Receta  # noqa: E402
from logica.ordenamiento import (busqueda_secuencial, busqueda_secuencial_todos, merge_sort,  # noqa: E402
                                 normalizar, ordenamiento_externo, ordenamiento_insercion)

# --- Datos del enunciado (copiados aquí para no depender de la base de datos)
_TABLA = [  # nombre, costo, unidad, personas por envase
    ("Cebolla", 500, "unidad", 4), ("Arroz", 1500, "paquete", 10),
    ("Tuto de pollo", 1200, "unidad", 1), ("Carne molida", 1500, "paquete", 4),
    ("Papa", 1000, "kg", 4), ("Tomate", 1500, "kg", 6), ("Fideos", 1200, "paquete", 4),
    ("Lechuga", 1000, "unidad", 10), ("Huevo", 4500, "empaque", 12), ("Aceite", 1000, "litro", 10),
]
ING = {n: Ingrediente(i, n, c, u, r) for i, (n, c, u, r) in enumerate(_TABLA, start=1)}
_RECETAS = {
    "Arroz con Pollo y Ensalada": ["Tuto de pollo", "Arroz", "Lechuga", "Aceite"],
    "Carne Molida con Papas y Arroz": ["Carne molida", "Papa", "Cebolla", "Aceite"],
    "Tallarines con Salsa de Tomate": ["Fideos", "Tomate", "Cebolla", "Aceite"],
    "Tortilla de Papas y Cebolla": ["Papa", "Cebolla", "Huevo", "Aceite"],
    "Pollo Salteado con Verduras": ["Tuto de pollo", "Tomate", "Cebolla", "Aceite"],
    "Charquicán Simple": ["Papa", "Lechuga", "Cebolla", "Aceite"],
    "Fideos con Huevo y Tomate": ["Fideos", "Huevo", "Tomate", "Aceite"],
    "Carne Molida con Arroz y Ensalada": ["Carne molida", "Arroz", "Lechuga", "Tomate"],
    "Papas Cocidas con Huevo y Lechuga": ["Papa", "Huevo", "Lechuga", "Aceite"],
    "Arroz Graneado con Huevo y Cebolla": ["Arroz", "Huevo", "Cebolla", "Aceite"],
}
RECETAS = [Receta(i, nombre, 4, [LineaReceta(ING[x], 4, "porciones") for x in lista])
           for i, (nombre, lista) in enumerate(_RECETAS.items(), start=1)]
TORTILLA = RECETAS[3]

random.seed(2026)


# ==========================================================================
# Motor de cálculo
# ==========================================================================
def test_ejemplo_tortilla_10_comensales():
    orden = calculo.calcular_orden(TORTILLA, 10)
    d = {x.ingrediente.nombre: x for x in orden.detalles}
    assert (d["Papa"].envases, d["Papa"].merma_fisica, d["Papa"].perdida) == (3, Fraction(1, 2), 500)
    assert (d["Cebolla"].envases, d["Cebolla"].porciones_sobrantes, d["Cebolla"].perdida) == (3, 2, 250)
    assert (d["Huevo"].envases, d["Huevo"].porciones_sobrantes, d["Huevo"].perdida) == (1, 2, 750)
    assert (d["Aceite"].envases, d["Aceite"].perdida) == (1, 0)
    assert d["Papa"].cantidad_requerida == Fraction(5, 2)
    assert orden.costo_total == 10000 and orden.perdida_total == 1500
    assert orden.costo_por_plato == 1000 and orden.precio_venta_plato == 1250
    assert orden.venta_total == 12500 and orden.costo_aprovechado == 8500


def test_costo_por_plato_no_entero():
    orden = calculo.calcular_orden(TORTILLA, 3)        # papa 1, cebolla 1, huevo 1, aceite 1
    assert orden.costo_total == 1000 + 500 + 4500 + 1000
    assert orden.costo_por_plato == Fraction(7000, 3)
    assert calculo.a_pesos(orden.costo_por_plato) == 2333.33
    orden = calculo.calcular_orden(RECETAS[0], 7)      # pollo 7, arroz 1, lechuga 1, aceite 1
    assert orden.costo_total == 7 * 1200 + 1500 + 1000 + 1000
    assert orden.costo_por_plato == Fraction(11900, 7)
    assert calculo.a_pesos(orden.costo_por_plato) == 1700.0
    assert calculo.a_pesos(orden.precio_venta_plato) == 2125.0
    orden = calculo.calcular_orden(RECETAS[2], 7)      # tallarines: 3.1 periódico
    assert calculo.a_pesos(orden.costo_por_plato) == round(orden.costo_total / 7, 2)


def _verificacion_independiente(receta, n):
    """Otro método: abre envases de a uno mientras falten porciones."""
    envases = sobrantes = costo = 0
    perdida = Fraction(0)
    detalle = {}
    for linea in receta.lineas:
        ing = linea.ingrediente
        abiertos, disponibles = 0, 0
        while disponibles < n:
            abiertos += 1
            disponibles += ing.rendimiento
        sobra = disponibles - n
        detalle[ing.nombre] = (abiertos, sobra)
        envases += abiertos
        sobrantes += sobra
        costo += abiertos * ing.costo_envase
        perdida += Fraction(sobra * ing.costo_envase, ing.rendimiento)
    return detalle, costo, perdida


def test_motor_contra_metodo_independiente():
    for receta in RECETAS:
        for n in range(1, 121):
            orden = calculo.calcular_orden(receta, n)
            detalle, costo, perdida = _verificacion_independiente(receta, n)
            for x in orden.detalles:
                assert (x.envases, x.porciones_sobrantes) == detalle[x.ingrediente.nombre], (receta.nombre, n)
                assert x.porciones_sobrantes < x.ingrediente.rendimiento          # nunca sobra un envase entero
                assert x.cantidad_requerida + x.merma_fisica == x.envases
            assert orden.costo_total == costo and orden.perdida_total == perdida
            assert orden.costo_por_plato * n == orden.costo_total
            assert orden.precio_venta_plato == orden.costo_por_plato * Fraction(5, 4)
            assert orden.venta_total == orden.costo_total * Fraction(5, 4)
            assert 0 <= orden.perdida_total < orden.costo_total


def test_validaciones_de_comensales():
    for malo in (None, "", "   ", 0, "0", -3, "-3", 2.5, "2,5", "abc", True, 1001, float("nan")):
        try:
            calculo.validar_comensales(malo)
        except ErrorValidacion:
            continue
        raise AssertionError(f"debió rechazar {malo!r}")
    assert calculo.validar_comensales(1) == 1
    assert calculo.validar_comensales("25") == 25
    assert calculo.validar_comensales(25.0) == 25
    assert calculo.validar_comensales(1000) == 1000
    try:
        calculo.calcular_orden(Receta(99, "Vacía", 4, []), 5)
        raise AssertionError("receta sin ingredientes")
    except ErrorValidacion:
        pass


def test_mensajes_distinguen_cero_y_negativo():
    for valor, texto in ((0, "cero"), (-1, "negativa"), (None, "Ingrese")):
        try:
            calculo.validar_comensales(valor)
        except ErrorValidacion as e:
            assert texto in str(e), str(e)


def test_comensales_sin_merma():
    assert calculo.comensales_sin_merma(TORTILLA) == 60
    for receta in RECETAS:
        mcm = calculo.comensales_sin_merma(receta)
        assert calculo.calcular_orden(receta, mcm).perdida_total == 0
        for n in range(1, mcm):
            assert calculo.calcular_orden(receta, n).perdida_total > 0
    filas = calculo.simular_comensales(TORTILLA, 1, 60)
    assert len(filas) == 60 and filas[-1]["perdida_total"] == 0


def test_redondeo_a_pesos():
    assert calculo.a_pesos(Fraction(4400, 3)) == 1466.67
    assert calculo.a_pesos(Fraction(1, 8)) == 0.13
    assert calculo.a_pesos(Fraction(5, 2)) == 2.5


# ==========================================================================
# Estructuras de datos
# ==========================================================================
def _falla(funcion):
    try:
        funcion()
    except IndexError:
        return True
    return False


def test_pila_y_cola():
    p = Pila()
    for x in (1, 2, 3):
        p.apilar(x)
    assert list(p) == [3, 2, 1] and p.cima() == 3 and len(p) == 3
    assert p.desapilar() == 3 and p.desapilar() == 2 and p.desapilar() == 1
    assert p.esta_vacia() and _falla(p.desapilar) and _falla(p.cima)
    c = Cola()
    for x in ("a", "b", "c"):
        c.encolar(x)
    assert list(c) == ["a", "b", "c"] and c.frente() == "a"
    assert c.desencolar() == "a" and c.desencolar() == "b" and len(c) == 1
    assert c.desencolar() == "c" and c.esta_vacia() and _falla(c.desencolar) and _falla(c.frente)


def test_cola_prioridad():
    datos = [random.randint(0, 50) for _ in range(500)]
    for mayor_primero in (False, True):
        cola = ColaPrioridad(mayor_primero=mayor_primero)
        for i, x in enumerate(datos):
            cola.insertar((x, i), x)
        salida = [cola.extraer() for _ in range(len(datos))]
        esperado = sorted(((x, i) for i, x in enumerate(datos)), key=lambda t: t[0], reverse=mayor_primero)
        assert salida == esperado          # mismo orden que sorted() estable: respeta la llegada en empates
    assert _falla(ColaPrioridad().extraer) and _falla(ColaPrioridad().ver)
    registros = [{"id": i, "p": random.choice([0, 250, 500, 750])} for i in range(60)]
    top = mayores(registros, lambda r: r["p"], 7)
    assert top == sorted(registros, key=lambda r: r["p"], reverse=True)[:7]


def test_arbol_binario_busqueda():
    datos = [(random.randint(0, 40), i) for i in range(400)]
    abb = ArbolBinarioBusqueda()
    for clave, i in datos:
        abb.insertar(clave, (clave, i))
    assert len(abb) == 400
    assert abb.inorden() == sorted(datos, key=lambda t: t[0])
    assert abb.inorden(descendente=True) == sorted(datos, key=lambda t: t[0], reverse=True)
    assert abb.rango(10, 20) == sorted([t for t in datos if 10 <= t[0] <= 20], key=lambda t: t[0])
    assert abb.rango(41, 99) == [] and abb.rango(-5, -1) == []
    assert abb.buscar(7) == [t for t in datos if t[0] == 7] and abb.buscar(999) == []
    degenerado = ArbolBinarioBusqueda()             # claves ya ordenadas: altura n, sin recursión
    for k in range(3000):
        degenerado.insertar(k, k)
    assert degenerado.altura() == 3000 and degenerado.inorden()[:3] == [0, 1, 2]
    assert ArbolBinarioBusqueda().altura() == 0 and ArbolBinarioBusqueda().inorden() == []


def test_grafo_menu_ingrediente():
    g = Grafo()
    for receta in RECETAS:
        g.agregar_vertice(receta.nombre, "menu")
        for ing in receta.ingredientes():
            g.agregar_vertice(ing.nombre, "ingrediente")
            g.agregar_arista(receta.nombre, ing.nombre, 0)
    assert len(g.vertices("menu")) == 10 and len(g.vertices("ingrediente")) == 10
    assert g.grado("Aceite") == 9 and "Carne Molida con Arroz y Ensalada" not in g.vecinos("Aceite")
    assert sorted(g.vecinos("Tortilla de Papas y Cebolla")) == ["Aceite", "Cebolla", "Huevo", "Papa"]
    g.sumar_peso("Tortilla de Papas y Cebolla", "Huevo", 750)
    g.sumar_peso("Fideos con Huevo y Tomate", "Huevo", 375)
    assert g.peso("Huevo", "Tortilla de Papas y Cebolla") == 750 and g.grado_ponderado("Huevo") == 1125
    distancias = dict(g.recorrido_anchura("Carne Molida con Arroz y Ensalada", max_saltos=2))
    relacionados = {v for v, d in distancias.items() if d == 2 and g.tipo(v) == "menu"}
    assert relacionados == {r.nombre for r in RECETAS
                            if r.nombre != "Carne Molida con Arroz y Ensalada"
                            and {"Carne molida", "Arroz", "Lechuga", "Tomate"} & {i.nombre for i in r.ingredientes()}}
    assert g.recorrido_anchura("No existe") == []


# ==========================================================================
# Ordenamiento y búsqueda
# ==========================================================================
def _registros(n):
    return [{"id": i, "menu": random.choice(list(_RECETAS)), "perdida": random.choice([0, 250, 375, 500, 1250]),
             "fecha": f"2026-11-{random.randint(10, 26):02d}T1{random.randint(0, 9)}:00:00+00:00"}
            for i in range(n)]


def test_ordenamientos_internos():
    for n in (0, 1, 2, 17, 300):
        datos = _registros(n)
        for campo in ("perdida", "menu", "fecha"):
            for desc in (False, True):
                esperado = sorted(datos, key=lambda r: r[campo], reverse=desc)
                assert merge_sort(datos, lambda r: r[campo], desc) == esperado
                assert ordenamiento_insercion(datos, lambda r: r[campo], desc) == esperado
    original = [3, 1, 2]
    merge_sort(original)
    assert original == [3, 1, 2]                    # no modifica la lista recibida


def test_ordenamiento_externo():
    datos = _registros(137)
    for tam in (1, 3, 10, 50, 500):
        for desc in (False, True):
            r = ordenamiento_externo(datos, "perdida", tam_bloque=tam, descendente=desc)
            assert r.registros == sorted(datos, key=lambda x: x["perdida"], reverse=desc)
            assert r.corridas == math.ceil(137 / tam)
    assert ordenamiento_externo([], "perdida").registros == []
    r = ordenamiento_externo(datos, "menu", tam_bloque=20)
    assert [x["id"] for x in r.registros] == [x["id"] for x in sorted(datos, key=lambda x: x["menu"])]


def test_busqueda_secuencial():
    usuarios = [{"usuario": "cocina"}, {"usuario": "administrador"}]
    assert busqueda_secuencial(usuarios, lambda u: u["usuario"] == "administrador") == (usuarios[1], 2)
    assert busqueda_secuencial(usuarios, lambda u: u["usuario"] == "otro") == (None, 2)
    insumos = list(ING.values())
    assert [i.nombre for i in busqueda_secuencial_todos(insumos, lambda i: "pa" in normalizar(i.nombre))] == ["Papa"]
    assert normalizar("  CEBOLLÁ ") == "cebolla" and normalizar(None) == ""
    assert {i.nombre for i in busqueda_secuencial_todos(insumos, lambda i: "o" in normalizar(i.nombre))} >= {"Tomate", "Huevo"}


# ==========================================================================
if __name__ == "__main__":
    pruebas = [(nombre, f) for nombre, f in sorted(globals().items()) if nombre.startswith("test_")]
    for nombre, funcion in pruebas:
        funcion()
        print(f"  ok  {nombre}")
    print(f"\n{len(pruebas)} pruebas aprobadas.")
