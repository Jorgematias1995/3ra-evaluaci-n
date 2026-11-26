"""
==========================================================================
 Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
 Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
--------------------------------------------------------------------------
 Archivo  : logica/estructuras.py
 Propósito: Tipos de datos abstractos (TDA) usados por el sistema.
 Librerías: collections.deque (biblioteca estándar de Python)
==========================================================================

Dónde se usa cada estructura y por qué:

  Pila (LIFO)          vistas/cocina.py: órdenes registradas en la sesión.
                       "Deshacer" anula la ÚLTIMA registrada (como Ctrl+Z).
                       También sirve para recorrer el árbol sin recursión.
  Cola (FIFO)          vistas/cocina.py: cola de preparación. Las órdenes se
                       preparan en el mismo orden en que llegaron.
  ColaPrioridad        Ranking de mayores pérdidas por merma (panel y análisis)
  (montículo binario)  y mezcla de corridas del ordenamiento externo.
  ArbolBinarioBusqueda Análisis de mermas: órdenes jerarquizadas por pérdida
                       y consulta por rango de pérdida.
  Grafo                Relación menú-ingrediente: qué menús usan un insumo,
                       qué menús comparten insumos y cuánta pérdida acumula
                       cada par menú-ingrediente.
"""
from __future__ import annotations

from collections import deque


# ==========================================================================
# PILA (LIFO: el último en entrar es el primero en salir)
# ==========================================================================
class Pila:
    """Pila sobre una lista de Python. Se apila y desapila por el FINAL de la
    lista porque append() y pop() en el final son O(1)."""

    def __init__(self):
        self._elementos = []

    def apilar(self, elemento) -> None:
        self._elementos.append(elemento)

    def desapilar(self):
        if self.esta_vacia():
            raise IndexError("La pila está vacía")
        return self._elementos.pop()

    def cima(self):
        """Mira el elemento de arriba sin sacarlo."""
        if self.esta_vacia():
            raise IndexError("La pila está vacía")
        return self._elementos[-1]

    def esta_vacia(self) -> bool:
        return len(self._elementos) == 0

    def __len__(self) -> int:
        return len(self._elementos)

    def __iter__(self):
        """Recorre de la cima al fondo (de la más reciente a la más antigua)."""
        return reversed(self._elementos)


# ==========================================================================
# COLA (FIFO: el primero en entrar es el primero en salir)
# ==========================================================================
class Cola:
    """Cola sobre collections.deque. Se eligió deque porque agrega por el final
    y saca por el inicio en O(1); con una lista, pop(0) es O(n) porque corre
    todos los elementos una posición."""

    def __init__(self):
        self._elementos = deque()

    def encolar(self, elemento) -> None:
        self._elementos.append(elemento)

    def desencolar(self):
        if self.esta_vacia():
            raise IndexError("La cola está vacía")
        return self._elementos.popleft()

    def frente(self):
        """Mira el primero de la fila sin sacarlo."""
        if self.esta_vacia():
            raise IndexError("La cola está vacía")
        return self._elementos[0]

    def esta_vacia(self) -> bool:
        return len(self._elementos) == 0

    def __len__(self) -> int:
        return len(self._elementos)

    def __iter__(self):
        """Recorre desde el frente hasta el final de la fila."""
        return iter(self._elementos)


# ==========================================================================
# COLA CON PRIORIDAD (montículo binario implementado a mano)
# ==========================================================================
class ColaPrioridad:
    """Montículo binario guardado en una lista (árbol completo por niveles):
    el padre de la posición i está en (i - 1) // 2 y sus hijos en 2i+1 y 2i+2.
    La raíz (posición 0) siempre es el elemento de mayor prioridad.

    insertar y extraer cuestan O(log n): solo recorren una rama del árbol.
    Para sacar los k mayores de n registros esto es más barato que ordenar todo.

    mayor_primero=True  -> sale primero la prioridad MÁS ALTA (ranking de pérdidas).
    mayor_primero=False -> sale primero la prioridad MÁS BAJA (mezcla del
                           ordenamiento externo en orden ascendente).
    Desempate: con prioridades iguales sale primero el de menor `desempate`
    (por defecto, el orden de llegada); así la cola es estable.
    """

    def __init__(self, mayor_primero: bool = False):
        self._datos = []          # cada nodo: (prioridad, desempate, elemento)
        self._mayor_primero = mayor_primero
        self._llegadas = 0        # contador para el desempate por orden de llegada

    # -- operaciones del TDA ------------------------------------------------
    def insertar(self, elemento, prioridad, desempate=None) -> None:
        if desempate is None:
            desempate = self._llegadas
        self._llegadas += 1
        self._datos.append((prioridad, desempate, elemento))
        self._subir(len(self._datos) - 1)

    def extraer(self):
        """Saca y devuelve el elemento de mayor prioridad."""
        if self.esta_vacia():
            raise IndexError("La cola con prioridad está vacía")
        raiz = self._datos[0]
        ultimo = self._datos.pop()
        if self._datos:                  # el último pasa a la raíz y "baja" a su lugar
            self._datos[0] = ultimo
            self._bajar(0)
        return raiz[2]

    def ver(self):
        """Mira el elemento de mayor prioridad sin sacarlo."""
        if self.esta_vacia():
            raise IndexError("La cola con prioridad está vacía")
        return self._datos[0][2]

    def esta_vacia(self) -> bool:
        return len(self._datos) == 0

    def __len__(self) -> int:
        return len(self._datos)

    # -- funcionamiento interno ---------------------------------------------
    def _va_antes(self, a, b) -> bool:
        """True si el nodo a debe quedar más arriba que el nodo b."""
        if a[0] != b[0]:
            return a[0] > b[0] if self._mayor_primero else a[0] < b[0]
        return a[1] < b[1]

    def _subir(self, i: int) -> None:
        """Después de insertar al final: intercambia con el padre mientras le gane."""
        while i > 0:
            padre = (i - 1) // 2
            if self._va_antes(self._datos[i], self._datos[padre]):
                self._datos[i], self._datos[padre] = self._datos[padre], self._datos[i]
                i = padre
            else:
                break

    def _bajar(self, i: int) -> None:
        """Después de extraer: intercambia con el mejor hijo mientras alguno le gane."""
        n = len(self._datos)
        while True:
            mejor = i
            for hijo in (2 * i + 1, 2 * i + 2):
                if hijo < n and self._va_antes(self._datos[hijo], self._datos[mejor]):
                    mejor = hijo
            if mejor == i:
                return
            self._datos[i], self._datos[mejor] = self._datos[mejor], self._datos[i]
            i = mejor


def mayores(elementos, clave, cantidad: int) -> list:
    """Los `cantidad` elementos con mayor clave, usando la cola con prioridad
    (ranking de las mayores pérdidas). Devuelve de mayor a menor."""
    cola = ColaPrioridad(mayor_primero=True)
    for elemento in elementos:
        cola.insertar(elemento, clave(elemento))
    resultado = []
    while not cola.esta_vacia() and len(resultado) < cantidad:
        resultado.append(cola.extraer())
    return resultado


# ==========================================================================
# ÁRBOL BINARIO DE BÚSQUEDA (ABB)
# ==========================================================================
class _NodoABB:
    __slots__ = ("clave", "valores", "izquierdo", "derecho")

    def __init__(self, clave, valor):
        self.clave = clave
        self.valores = [valor]   # claves repetidas (misma pérdida) comparten nodo
        self.izquierdo = None    # subárbol con claves MENORES
        self.derecho = None      # subárbol con claves MAYORES


class ArbolBinarioBusqueda:
    """ABB: para cada nodo, a la izquierda quedan las claves menores y a la
    derecha las mayores. Por eso el recorrido INORDEN (izquierda, nodo,
    derecha) entrega los registros ordenados por la clave.

    Se programó sin recursión (con la Pila y la Cola de este archivo): si las
    claves llegan casi ordenadas, el árbol se "degenera" en una lista de altura
    n y una versión recursiva podría superar el límite de recursión de Python.
    """

    def __init__(self):
        self._raiz = None
        self._cantidad = 0

    def insertar(self, clave, valor) -> None:
        self._cantidad += 1
        if self._raiz is None:
            self._raiz = _NodoABB(clave, valor)
            return
        actual = self._raiz
        while True:
            if clave == actual.clave:
                actual.valores.append(valor)
                return
            if clave < actual.clave:
                if actual.izquierdo is None:
                    actual.izquierdo = _NodoABB(clave, valor)
                    return
                actual = actual.izquierdo
            else:
                if actual.derecho is None:
                    actual.derecho = _NodoABB(clave, valor)
                    return
                actual = actual.derecho

    def buscar(self, clave) -> list:
        """Valores con exactamente esa clave. En cada paso descarta la mitad
        del árbol que no puede contenerla (O(altura))."""
        actual = self._raiz
        while actual is not None:
            if clave == actual.clave:
                return list(actual.valores)
            actual = actual.izquierdo if clave < actual.clave else actual.derecho
        return []

    def inorden(self, descendente: bool = False) -> list:
        """Todos los valores ordenados por clave, usando una Pila explícita."""
        resultado = []
        pila = Pila()
        actual = self._raiz
        while actual is not None or not pila.esta_vacia():
            while actual is not None:                     # bajar todo lo posible
                pila.apilar(actual)
                actual = actual.derecho if descendente else actual.izquierdo
            actual = pila.desapilar()                     # visitar el nodo
            resultado.extend(actual.valores)
            actual = actual.izquierdo if descendente else actual.derecho
        return resultado

    def rango(self, minimo, maximo) -> list:
        """Valores con minimo <= clave <= maximo, en orden ascendente.
        Poda: no baja por ramas que solo tienen claves fuera del rango."""
        resultado = []
        pila = Pila()
        actual = self._raiz
        while actual is not None or not pila.esta_vacia():
            while actual is not None:
                pila.apilar(actual)
                # a la izquierda solo hay claves menores: si esta ya es <= minimo, no sirven
                actual = actual.izquierdo if actual.clave > minimo else None
            actual = pila.desapilar()
            if actual.clave > maximo:   # inorden es creciente: lo que sigue es aún mayor
                break
            if actual.clave >= minimo:
                resultado.extend(actual.valores)
            actual = actual.derecho
        return resultado

    def altura(self) -> int:
        """Niveles del árbol, recorriéndolo por niveles con una Cola."""
        if self._raiz is None:
            return 0
        niveles = 0
        cola = Cola()
        cola.encolar(self._raiz)
        while not cola.esta_vacia():
            niveles += 1
            for _ in range(len(cola)):                    # todos los nodos del nivel actual
                nodo = cola.desencolar()
                for hijo in (nodo.izquierdo, nodo.derecho):
                    if hijo is not None:
                        cola.encolar(hijo)
        return niveles

    def __len__(self) -> int:
        return self._cantidad


# ==========================================================================
# GRAFO (lista de adyacencia, no dirigido y con pesos)
# ==========================================================================
class Grafo:
    """Grafo guardado como lista de adyacencia: un diccionario que a cada
    vértice le asocia otro diccionario {vecino: peso}. Se eligió sobre una
    matriz de adyacencia porque el grafo menú-ingrediente tiene pocas aristas
    (cada menú usa 4 o 5 de los 10 insumos) y así solo se guarda lo que existe.

    Se usa como grafo BIPARTITO: vértices de tipo 'menu' y de tipo
    'ingrediente'; una arista indica que el menú usa ese ingrediente y su
    peso acumula la pérdida por merma de ese par.
    """

    def __init__(self):
        self._adyacencia = {}     # vértice -> {vecino: peso}
        self._tipos = {}          # vértice -> 'menu' o 'ingrediente'

    def agregar_vertice(self, vertice, tipo=None) -> None:
        self._adyacencia.setdefault(vertice, {})
        if tipo is not None:
            self._tipos[vertice] = tipo

    def agregar_arista(self, u, v, peso=0) -> None:
        self.agregar_vertice(u)
        self.agregar_vertice(v)
        self._adyacencia[u][v] = peso     # no dirigido: se guarda en ambos sentidos
        self._adyacencia[v][u] = peso

    def sumar_peso(self, u, v, cantidad) -> None:
        """Acumula `cantidad` en la arista u-v (debe existir)."""
        self._adyacencia[u][v] += cantidad
        self._adyacencia[v][u] += cantidad

    def existe_arista(self, u, v) -> bool:
        return v in self._adyacencia.get(u, {})

    def peso(self, u, v):
        return self._adyacencia[u][v]

    def vecinos(self, vertice) -> list:
        return list(self._adyacencia.get(vertice, {}))

    def grado(self, vertice) -> int:
        """Cantidad de aristas del vértice (ej. en cuántos menús se usa un insumo)."""
        return len(self._adyacencia.get(vertice, {}))

    def grado_ponderado(self, vertice):
        """Suma de los pesos de sus aristas (ej. pérdida total de un insumo)."""
        return sum(self._adyacencia.get(vertice, {}).values())

    def vertices(self, tipo=None) -> list:
        return [v for v in self._adyacencia if tipo is None or self._tipos.get(v) == tipo]

    def tipo(self, vertice):
        return self._tipos.get(vertice)

    def recorrido_anchura(self, origen, max_saltos=None) -> list:
        """BFS desde `origen` con una Cola. Devuelve [(vértice, distancia), ...].
        En el grafo bipartito, los menús a distancia 2 de un menú son los que
        comparten al menos un ingrediente con él."""
        if origen not in self._adyacencia:
            return []
        distancia = {origen: 0}
        cola = Cola()
        cola.encolar(origen)
        while not cola.esta_vacia():
            actual = cola.desencolar()
            if max_saltos is not None and distancia[actual] >= max_saltos:
                continue
            for vecino in self._adyacencia[actual]:
                if vecino not in distancia:
                    distancia[vecino] = distancia[actual] + 1
                    cola.encolar(vecino)
        return list(distancia.items())
