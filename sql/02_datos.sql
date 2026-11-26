-- ==========================================================================
--  Evaluación N°3 · Programación Avanzada · I CRIM Sistemas de Armas
--  Alumno: Jorge Gómez Prado · Fecha: 26 de noviembre de 2026
-- --------------------------------------------------------------------------
--  02_datos.sql · Población inicial (Actividad 1)
--  Roles, 10 ingredientes y 10 recetas del enunciado (40 líneas de receta).
--  Re-ejecutable: "on conflict" actualiza en vez de duplicar.
--  Los USUARIOS no van aquí: se crean con scripts/crear_usuarios.py para que
--  ninguna contraseña (ni su hash) quede escrita en el repositorio.
-- ==========================================================================


-- Roles: qué puede ver cada perfil -----------------------------------------
insert into public.roles (nombre, descripcion, ve_costos, ve_panel) values
  ('cocina',        'Prepara los servicios: ve solo ingredientes y cantidades', false, false),
  ('administrador', 'Acceso total: costos, mermas, ventas e historial',         true,  true)
on conflict (nombre) do update
  set descripcion = excluded.descripcion,
      ve_costos   = excluded.ve_costos,
      ve_panel    = excluded.ve_panel;


-- Ingredientes: tabla del enunciado ----------------------------------------
-- costo_envase = "Costo (en $)"; rendimiento_personas = "Utilidad".
-- unidades_por_envase / nombre_unidad: equivalencias para mostrarle a cocina
-- cantidades físicas (son supuestos del alumno, ver columna supuesto).
insert into public.ingredientes
  (nombre, costo_envase, unidad_compra, rendimiento_personas, unidades_por_envase, nombre_unidad, supuesto)
values
  ('Cebolla',       500, 'unidad',   4, null, null, null),
  ('Arroz',        1500, 'paquete', 10, null, null, null),
  ('Tuto de pollo', 1200, 'unidad',  1, null, null,
   'Las recetas lo nombran "Pollo (trutro/pechuga)"; es el mismo insumo.'),
  ('Carne molida', 1500, 'paquete',  4, null, null, null),
  ('Papa',         1000, 'kg',       4,    4, 'papas',
   'Supuesto: 1 kg = 4 papas (1 papa por persona). Las recetas indican 6 papas para 4 comensales; el cálculo usa la tabla (4 personas por kg).'),
  ('Tomate',       1500, 'kg',       6,    4, 'tomates',
   '1 kg = 4 tomates. El cálculo usa la tabla (6 personas por kg): cada persona recibe 2/3 de tomate.'),
  ('Fideos',       1200, 'paquete',  4, null, null,
   'Las recetas los nombran "Fideos (espagueti)"; es el mismo insumo.'),
  ('Lechuga',      1000, 'unidad',  10, null, null,
   'La tabla indica 1 lechuga cada 10 personas; las recetas usan 1 para 4. El cálculo usa la tabla.'),
  ('Huevo',        4500, 'empaque', 12,   12, 'huevos',
   'Supuesto: 1 empaque = 12 huevos (1 huevo por persona).'),
  ('Aceite',       1000, 'litro',   10, 1000, 'ml',
   '1 litro rinde 10 porciones de 100 ml.')
on conflict (nombre) do update
  set costo_envase         = excluded.costo_envase,
      unidad_compra        = excluded.unidad_compra,
      rendimiento_personas = excluded.rendimiento_personas,
      unidades_por_envase  = excluded.unidades_por_envase,
      nombre_unidad        = excluded.nombre_unidad,
      supuesto             = excluded.supuesto;


-- Recetas (base: 4 comensales) ---------------------------------------------
insert into public.recetas (nombre, comensales_base, observacion) values
  ('Arroz con Pollo y Ensalada',         4, null),
  ('Carne Molida con Papas y Arroz',     4,
   'Esta receta no lleva arroz aunque el nombre lo mencione: se usa su lista de ingredientes.'),
  ('Tallarines con Salsa de Tomate',     4, null),
  ('Tortilla de Papas y Cebolla',        4, null),
  ('Pollo Salteado con Verduras',        4, null),
  ('Charquicán Simple',                  4, null),
  ('Fideos con Huevo y Tomate',          4, null),
  ('Carne Molida con Arroz y Ensalada',  4, null),
  ('Papas Cocidas con Huevo y Lechuga',  4, null),
  ('Arroz Graneado con Huevo y Cebolla', 4, null)
on conflict (nombre) do update
  set comensales_base = excluded.comensales_base,
      observacion     = excluded.observacion;


-- Ingredientes de cada receta, tal como los indica el enunciado ------------
-- Se cruzan por nombre (join) para no depender de los id generados.
insert into public.receta_ingredientes (receta_id, ingrediente_id, cantidad_base, unidad_receta)
select r.id, i.id, v.cantidad, v.unidad
from (values
  ('Arroz con Pollo y Ensalada',         'Tuto de pollo', 4, 'unidades'),
  ('Arroz con Pollo y Ensalada',         'Arroz',         4, 'porciones'),
  ('Arroz con Pollo y Ensalada',         'Lechuga',       1, 'unidades'),
  ('Arroz con Pollo y Ensalada',         'Aceite',        4, 'porciones'),

  ('Carne Molida con Papas y Arroz',     'Carne molida',  4, 'porciones'),
  ('Carne Molida con Papas y Arroz',     'Papa',          6, 'unidades'),
  ('Carne Molida con Papas y Arroz',     'Cebolla',       1, 'unidades'),
  ('Carne Molida con Papas y Arroz',     'Aceite',        4, 'porciones'),

  ('Tallarines con Salsa de Tomate',     'Fideos',        4, 'porciones'),
  ('Tallarines con Salsa de Tomate',     'Tomate',        4, 'unidades'),
  ('Tallarines con Salsa de Tomate',     'Cebolla',       1, 'unidades'),
  ('Tallarines con Salsa de Tomate',     'Aceite',        4, 'porciones'),

  ('Tortilla de Papas y Cebolla',        'Papa',          6, 'unidades'),
  ('Tortilla de Papas y Cebolla',        'Cebolla',       1, 'unidades'),
  ('Tortilla de Papas y Cebolla',        'Huevo',         6, 'unidades'),
  ('Tortilla de Papas y Cebolla',        'Aceite',        4, 'porciones'),

  ('Pollo Salteado con Verduras',        'Tuto de pollo', 4, 'unidades'),
  ('Pollo Salteado con Verduras',        'Tomate',        3, 'unidades'),
  ('Pollo Salteado con Verduras',        'Cebolla',       1, 'unidades'),
  ('Pollo Salteado con Verduras',        'Aceite',        4, 'porciones'),

  ('Charquicán Simple',                  'Papa',          6, 'unidades'),
  ('Charquicán Simple',                  'Lechuga',       1, 'unidades'),
  ('Charquicán Simple',                  'Cebolla',       1, 'unidades'),
  ('Charquicán Simple',                  'Aceite',        4, 'porciones'),

  ('Fideos con Huevo y Tomate',          'Fideos',        4, 'porciones'),
  ('Fideos con Huevo y Tomate',          'Huevo',         4, 'unidades'),
  ('Fideos con Huevo y Tomate',          'Tomate',        3, 'unidades'),
  ('Fideos con Huevo y Tomate',          'Aceite',        4, 'porciones'),

  ('Carne Molida con Arroz y Ensalada',  'Carne molida',  4, 'porciones'),
  ('Carne Molida con Arroz y Ensalada',  'Arroz',         4, 'porciones'),
  ('Carne Molida con Arroz y Ensalada',  'Lechuga',       1, 'unidades'),
  ('Carne Molida con Arroz y Ensalada',  'Tomate',        2, 'unidades'),

  ('Papas Cocidas con Huevo y Lechuga',  'Papa',          6, 'unidades'),
  ('Papas Cocidas con Huevo y Lechuga',  'Huevo',         4, 'unidades'),
  ('Papas Cocidas con Huevo y Lechuga',  'Lechuga',       1, 'unidades'),
  ('Papas Cocidas con Huevo y Lechuga',  'Aceite',        4, 'porciones'),

  ('Arroz Graneado con Huevo y Cebolla', 'Arroz',         4, 'porciones'),
  ('Arroz Graneado con Huevo y Cebolla', 'Huevo',         4, 'unidades'),
  ('Arroz Graneado con Huevo y Cebolla', 'Cebolla',       1, 'unidades'),
  ('Arroz Graneado con Huevo y Cebolla', 'Aceite',        4, 'porciones')
) as v (receta, ingrediente, cantidad, unidad)
join public.recetas      r on r.nombre = v.receta
join public.ingredientes i on i.nombre = v.ingrediente
on conflict (receta_id, ingrediente_id) do update
  set cantidad_base = excluded.cantidad_base,
      unidad_receta = excluded.unidad_receta;


-- Verificación rápida (debe mostrar 2 · 10 · 10 · 40) ----------------------
select (select count(*) from public.roles)               as roles,
       (select count(*) from public.ingredientes)        as ingredientes,
       (select count(*) from public.recetas)             as recetas,
       (select count(*) from public.receta_ingredientes) as lineas_receta;
