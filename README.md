# Noches alegres, mañanas tristes · Gestión de cocina

**Evaluación N°3 · Programación Avanzada** · I CRIM Sistemas de Armas · Academia Politécnica Militar
Profesor: Dr. Carlos Santibáñez Rodríguez · Alumno: Cap. Jorge Gómez Prado · 26 de noviembre de 2026

Aplicación en Python + Streamlit + Supabase para la cocina del local **«Noches alegres, mañanas tristes»**.
Cocina ingresa el **menú** y la **cantidad de comensales**;
el sistema calcula los envases completos de cada ingrediente (productos indivisibles que no se pueden
guardar), la **merma** y su costo, el **costo real por plato** y el **precio de venta con 25 % de
ganancia**, y guarda la operación completa en Supabase.

| Perfil | Ve | No ve |
|---|---|---|
| `cocina` | Orden de preparación (ingredientes y cantidades), cola de preparación, sus órdenes de la sesión, consulta de insumos | Costos, pérdidas por merma, precios, panel |
| `administrador` | Todo: panel gerencial (KPIs), historial filtrable, análisis de mermas, catálogo y supuestos, y la vista de cocina con su detalle financiero | — |

## Regla de cálculo

Cada comensal consume **una porción** de cada ingrediente del menú, y la columna «Utilidad» de la tabla
indica cuántas porciones (personas) rinde un envase. Para N comensales:

```
envases            = ceil(N / rendimiento)                 (math.ceil: no se abre medio envase)
sobrantes          = envases × rendimiento − N             (no se pueden guardar: son merma)
merma física       = sobrantes / rendimiento               (en kg, paquetes, empaques, litros...)
pérdida por merma  = merma física × costo del envase
costo total        = Σ envases × costo del envase
costo real/plato   = costo total / N                       (incluye lo que se pierde)
precio de venta    = costo real por plato × 1,25           (25 % de ganancia sobre el costo)
```

Ejemplo, *Tortilla de Papas y Cebolla* para 10 comensales:

| Insumo | Envases | Costo | Sobra | Pérdida |
|---|---|---|---|---|
| Papa (4 personas/kg) | ceil(10/4) = 3 kg | $3.000 | 0,5 kg | $500 |
| Cebolla (4 personas/unidad) | ceil(10/4) = 3 | $1.500 | 0,5 cebolla | $250 |
| Huevo (12 personas/empaque) | ceil(10/12) = 1 | $4.500 | 2 huevos | $750 |
| Aceite (10 personas/litro) | ceil(10/10) = 1 L | $1.000 | 0 | $0 |
| **Total** | | **$10.000** | | **$1.500** |

Costo real por plato $1.000 → precio de venta **$1.250** por plato.

## Supuestos

1. **Se calcula con la tabla de ingredientes (rendimiento), no con las cantidades de las recetas.** Las dos
   fuentes del enunciado no calzan: la lechuga rinde 10 personas en la tabla y las recetas usan 1 para 4. Las recetas definen **qué** lleva cada
   menú; sus cantidades (base 4 comensales) quedan guardadas en `receta_ingredientes` como referencia.
2. **Papa: 1 kg = 4 papas** (1 papa por persona, igual que la tabla). Las recetas indican 6 papas para 4 comensales.
3. **Tomate: 1 kg = 4 tomates.** La tabla indica 6 personas por kg, así que cada persona recibe 2/3 de tomate.
   **Huevo: 1 empaque = 12 huevos** (1 por persona) y **Aceite: 1 litro = 10 porciones de 100 ml**. Estas
   equivalencias solo se usan para mostrarle a cocina cantidades físicas («2,5 kg ≈ 10 papas»).
4. **Carne Molida con Papas y Arroz no lleva arroz**, aunque el nombre lo mencione: se usa la lista de
   ingredientes de la receta.
5. «Tuto de pollo» (tabla) = «Pollo (trutro/pechuga)» (recetas); «Fideos» = «Fideos (espagueti)».
6. Cada orden abre sus propios envases: lo que sobra no pasa a la orden siguiente.
7. Máximo 1.000 comensales por servicio (evita errores de tipeo).
8. Una orden **anulada** por cocina («deshacer») queda en el historial, pero no cuenta en los indicadores.

## Estructura del proyecto

Lógica de cálculo, consultas a la base de datos e interfaz están separadas:

```
app.py                      Entrada: ingreso, sesión y menú según el rol (encabezado con los datos del alumno)
logica/                     Python puro (sin Streamlit ni Supabase)
  modelos.py                Clases Ingrediente, LineaReceta, Receta, DetalleInsumo, Orden
  estructuras.py            Pila, Cola, ColaPrioridad (montículo), ArbolBinarioBusqueda, Grafo
  ordenamiento.py           Inserción, merge sort, ordenamiento externo, búsqueda secuencial
  calculo.py                Motor de cálculo (Actividad 2)
  analisis.py               KPIs, agrupaciones y rankings del administrador
  supuestos.py              Supuestos que muestra la app
datos/
  base_datos.py             Única capa que consulta y escribe en Supabase
seguridad/
  claves.py                 Hash PBKDF2-SHA256 con sal de las contraseñas
  autenticacion.py          Ingreso (búsqueda secuencial), sesión, permisos y bloqueo por intentos
vistas/                     Páginas de Streamlit
  ingreso.py  cocina.py  panel.py  historial.py  mermas.py  catalogo.py  graficos.py  formato.py  encabezado.py
assets/                     Imagen junto al título del panel gerencial (gerencia.jpg)
sql/
  01_esquema.sql            Tablas, llaves, restricciones, índices y RLS (Actividad 1)
  02_datos.sql              Roles, 10 ingredientes, 10 recetas (40 líneas)
scripts/
  crear_usuarios.py         Crea los usuarios cocina y administrador (pide las contraseñas)
tests/
  test_logica.py            Pruebas del cálculo, estructuras y algoritmos (sin conexión)
.streamlit/
  config.toml               Apariencia
  secrets.toml.example      Plantilla de credenciales (el secrets.toml real NO se sube)
requirements.txt
```

## Puesta en marcha (VS Code)

1. **Supabase.** Cree un proyecto. En **SQL Editor** ejecute `sql/01_esquema.sql` y luego `sql/02_datos.sql`
   (al final muestra `2 · 10 · 10 · 40`).
2. **Credenciales.** Copie `.streamlit/secrets.toml.example` como `.streamlit/secrets.toml` y pegue la URL del
   proyecto y la **secret key** (Project Settings → API Keys).
3. **Entorno e instalación** (en la terminal de VS Code, dentro de la carpeta del proyecto):
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. **Usuarios:** `python scripts/crear_usuarios.py` (pide la contraseña de `cocina` y de `administrador`).
5. **Pruebas (opcional):** `python tests/test_logica.py`
6. **Ejecutar:** `streamlit run app.py`

Para Streamlit Community Cloud: *Main file path* `app.py` y, en *Advanced settings → Secrets*, el contenido de
`secrets.toml`.

## Dónde está cada requisito

| Actividad | Dónde |
|---|---|
| 1. Catálogo: 10 ingredientes y 10 recetas | `sql/02_datos.sql` |
| 1. Tablas de órdenes y mermas | `sql/01_esquema.sql`: `ordenes` (servicio y totales) y `orden_detalle` (por insumo: envases, sobrantes, merma física, costo, pérdida) |
| 1. Usuarios y roles | Tablas `roles` (permisos `ve_costos`, `ve_panel`) y `usuarios` (hash de la clave) |
| 2. Envases indivisibles con `math.ceil` | `logica/calculo.py` → `calcular_insumo()` |
| 2. Merma física y pérdida en pesos | `logica/calculo.py` → `calcular_insumo()` |
| 2. Costo por plato y venta +25 % | `logica/calculo.py` → `calcular_orden()` (`MARGEN_GANANCIA`) |
| 3. Control de acceso de cocina | `app.py` (menú por rol), `seguridad/autenticacion.py`, `vistas/cocina.py` (montos solo si `ve_costos`) |
| 3. Formulario validado (nulo, cero, negativo) | `vistas/cocina.py` → `_registrar()` y `logica/calculo.py` → `validar_comensales()` |
| 3. Orden de preparación y guardado automático | `vistas/cocina.py` → `_mostrar_orden()`, `datos/base_datos.py` → `guardar_orden()` |
| 4. KPIs (servicios, costo, merma, ingresos) | `vistas/panel.py`, `logica/analisis.py` → `indicadores()` |
| 4. Historial filtrable con desglose | `vistas/historial.py` |
| 4. Análisis de desechos | `vistas/mermas.py` (por menú, por insumo, mapa menú×insumo, rankings, simulador) |
| 5. Credenciales con `st.secrets` | `datos/base_datos.py` → `cliente()`; `.gitignore` excluye `secrets.toml` |
| 5. Código modular y comentado | Capas `logica/`, `datos/`, `seguridad/`, `vistas/`; encabezado en cada archivo |

## Estructuras de datos y algoritmos

| Contenido | Dónde se usa | Por qué |
|---|---|---|
| Clases / TDA | `logica/modelos.py` | Modelan ingredientes, recetas y órdenes |
| Lista | `Receta.lineas`, catálogos | Ingredientes de cada menú |
| Cola (FIFO) | Cola de preparación de cocina | Las órdenes se preparan en orden de llegada |
| Pila (LIFO) | «Mis órdenes» de cocina | «Deshacer» anula la última registrada |
| Cola con prioridad (montículo) | Rankings de pérdida; mezcla del ordenamiento externo | Saca los k mayores en O(log n) cada uno |
| Árbol binario de búsqueda | Análisis de mermas: órdenes por rango de pérdida | El recorrido inorden entrega las órdenes ordenadas |
| Grafo (lista de adyacencia) | Relación menú–insumo | Qué menús usan un insumo, menús relacionados, pérdida por par |
| Ordenamiento interno | Inserción (ingredientes de una orden) y merge sort (historial) | Inserción para listas cortas; merge sort O(n log n) y estable |
| Ordenamiento externo | Exportación del historial | Ordena por bloques en archivos temporales y los mezcla |
| Búsqueda secuencial | Validar el usuario al ingresar; consultar insumos | No requiere datos ordenados |

## Seguridad

- La URL y la secret key se leen con `st.secrets` desde `.streamlit/secrets.toml`, excluido por `.gitignore`.
- Las contraseñas se guardan como hash PBKDF2-SHA256 (200.000 iteraciones, sal aleatoria) y se comparan en tiempo constante.
- Tras 5 intentos fallidos el ingreso se bloquea 30 segundos; el mensaje de error no dice si falló el usuario o la clave.
- RLS activado en todas las tablas: la clave pública no puede leer ni escribir nada; solo la app (desde el servidor) accede.
- Cada página de administración vuelve a verificar el permiso, aunque el menú ya la oculte.
