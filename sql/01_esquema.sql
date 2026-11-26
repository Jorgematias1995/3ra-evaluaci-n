-- ==========================================================================
--  Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
--  Academia Politécnica Militar · Prof. Dr. Carlos Santibáñez Rodríguez
--  Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
-- --------------------------------------------------------------------------
--  01_esquema.sql · Modelo de datos (Actividad 1)
--  Ejecutar en Supabase -> SQL Editor (primero este archivo, luego 02_datos.sql).
--  Es re-ejecutable: usa "if not exists" y no borra datos.
--
--  Modelo entidad-relación (1 ──< N):
--
--    roles        1 ──< N usuarios              cada usuario tiene un rol
--    usuarios     1 ──< N ordenes               quién registró el servicio
--    recetas      1 ──< N ordenes               menú solicitado
--    ordenes      1 ──< N orden_detalle         un renglón por insumo de la orden
--    ingredientes 1 ──< N orden_detalle
--    recetas      1 ──< N receta_ingredientes N >── 1 ingredientes   (muchos a muchos)
--
--  * receta_ingredientes resuelve la relación muchos-a-muchos receta-ingrediente
--    (qué lleva cada menú y en qué cantidad según el enunciado).
--  * ordenes guarda cada servicio solicitado (menú, comensales y totales calculados).
--  * orden_detalle guarda, por cada insumo de la orden, los envases usados,
--    los sobrantes (merma física) y su costo/pérdida.
-- ==========================================================================


-- --------------------------------------------------------------------------
-- 1) Roles y usuarios (Gestión de Usuarios y Roles)
--    Los permisos viven en la base de datos, no en el código: la app lee
--    ve_costos y ve_panel del rol del usuario que ingresa.
-- --------------------------------------------------------------------------
create table if not exists public.roles (
  nombre      varchar(20) primary key,
  descripcion text        not null,
  ve_costos   boolean     not null default false,  -- costos, pérdidas por merma, precios
  ve_panel    boolean     not null default false   -- panel gerencial, historial y análisis
);

create table if not exists public.usuarios (
  id         integer generated always as identity primary key,
  usuario    varchar(30)  not null unique check (usuario = lower(usuario)),
  nombre     varchar(100) not null,
  rol        varchar(20)  not null references public.roles (nombre),
  clave_hash text         not null,                -- PBKDF2-SHA256 con sal; nunca la clave
  activo     boolean      not null default true,
  creado_en  timestamptz  not null default now()
);


-- --------------------------------------------------------------------------
-- 2) Catálogo: ingredientes y recetas (Población inicial del catálogo)
-- --------------------------------------------------------------------------
-- Un "envase" es la unidad de compra indivisible de la tabla del enunciado
-- (1 cebolla, 1 paquete, 1 kg, 1 empaque, 1 litro).
-- rendimiento_personas = columna "Utilidad": cuántas personas alcanza un envase.
create table if not exists public.ingredientes (
  id                   integer generated always as identity primary key,
  nombre               varchar(50) not null unique,
  costo_envase         integer     not null check (costo_envase > 0),
  unidad_compra        varchar(15) not null
                       check (unidad_compra in ('unidad', 'paquete', 'kg', 'empaque', 'litro')),
  rendimiento_personas integer     not null check (rendimiento_personas > 0),
  unidades_por_envase  integer     check (unidades_por_envase > 0),  -- equivalencia para cocina (ej. 4 papas por kg)
  nombre_unidad        varchar(20),                                  -- 'papas', 'tomates', 'huevos', 'ml'
  supuesto             text                                          -- supuesto o aclaración documentada
);

create table if not exists public.recetas (
  id              integer generated always as identity primary key,
  nombre          varchar(80) not null unique,
  comensales_base integer     not null default 4 check (comensales_base > 0),
  observacion     text
);

-- Relación muchos-a-muchos receta-ingrediente, con la cantidad tal como la
-- indica el enunciado para comensales_base (4 personas).
create table if not exists public.receta_ingredientes (
  receta_id      integer      not null references public.recetas (id) on delete cascade,
  ingrediente_id integer      not null references public.ingredientes (id),
  cantidad_base  numeric(6,2) not null check (cantidad_base > 0),
  unidad_receta  varchar(15)  not null check (unidad_receta in ('unidades', 'porciones')),
  primary key (receta_id, ingrediente_id)          -- un ingrediente no se repite en una receta
);


-- --------------------------------------------------------------------------
-- 3) Órdenes y mermas (Estructura de almacenamiento para órdenes y mermas)
-- --------------------------------------------------------------------------
-- Una fila por servicio solicitado por cocina, con los totales ya calculados
-- por la aplicación (logica/calculo.py) para que el panel no deba recalcular.
create table if not exists public.ordenes (
  id                 integer generated always as identity primary key,
  fecha              timestamptz   not null default now(),
  receta_id          integer       not null references public.recetas (id),
  usuario            varchar(30)   not null references public.usuarios (usuario),
  comensales         integer       not null check (comensales > 0 and comensales <= 1000),
  costo_total        integer       not null check (costo_total >= 0),        -- $ de todos los envases abiertos
  costo_por_plato    numeric(12,2) not null check (costo_por_plato >= 0),    -- costo_total / comensales
  precio_venta_plato numeric(12,2) not null check (precio_venta_plato >= 0), -- costo_por_plato x 1,25
  venta_total        numeric(14,2) not null check (venta_total >= 0),
  perdida_merma      numeric(12,2) not null check (perdida_merma >= 0),      -- $ de lo que sobra
  estado             varchar(12)   not null default 'pendiente'
                     check (estado in ('pendiente', 'preparada', 'anulada')),
  actualizado_en     timestamptz
);

-- Una fila por insumo de cada orden: el cálculo completo queda guardado.
create table if not exists public.orden_detalle (
  id                   integer generated always as identity primary key,
  orden_id             integer       not null references public.ordenes (id) on delete cascade,
  ingrediente_id       integer       not null references public.ingredientes (id),
  porciones_requeridas integer       not null check (porciones_requeridas > 0),
  envases              integer       not null check (envases > 0),          -- unidades completas (math.ceil)
  porciones_sobrantes  integer       not null check (porciones_sobrantes >= 0),
  merma_fisica         numeric(10,4) not null check (merma_fisica >= 0),     -- en unidad de compra (ej. 0,5 kg)
  costo                integer       not null check (costo >= 0),
  perdida_merma        numeric(12,2) not null check (perdida_merma >= 0),
  unique (orden_id, ingrediente_id)
);

-- Índices para las consultas del panel (por fecha, por menú y detalle de una orden)
create index if not exists ordenes_fecha_idx      on public.ordenes (fecha);
create index if not exists ordenes_receta_idx     on public.ordenes (receta_id);
create index if not exists ordenes_estado_idx     on public.ordenes (estado);
create index if not exists orden_detalle_orden_idx on public.orden_detalle (orden_id);


-- --------------------------------------------------------------------------
-- 4) Seguridad (RLS)
--    La app se conecta desde el servidor de Streamlit con la secret key
--    (guardada en .streamlit/secrets.toml, fuera del repositorio), que no
--    pasa por RLS. Con RLS activo y sin políticas, la clave pública (anon)
--    no puede leer ni escribir ninguna tabla: ni los hashes de las claves
--    ni los costos quedan expuestos fuera de la aplicación.
-- --------------------------------------------------------------------------
alter table public.roles               enable row level security;
alter table public.usuarios            enable row level security;
alter table public.ingredientes        enable row level security;
alter table public.recetas             enable row level security;
alter table public.receta_ingredientes enable row level security;
alter table public.ordenes             enable row level security;
alter table public.orden_detalle       enable row level security;

-- Permisos explícitos para la secret key (rol service_role de Supabase), por
-- si el proyecto no los otorga por defecto a las tablas nuevas. El bloque se
-- salta solo si el rol no existe (PostgreSQL fuera de Supabase).
do $$
begin
  if exists (select 1 from pg_roles where rolname = 'service_role') then
    grant usage on schema public to service_role;
    grant all on all tables in schema public to service_role;
    grant all on all sequences in schema public to service_role;
  end if;
end $$;
