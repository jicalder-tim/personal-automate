import cadquery as cq

# --- 1. CONFIGURACIÓN (TUS VARIABLES REGULABLES) ---

# Configuración de la Grilla
num_columnas = 10      # Cantidad de agujeros en X
num_filas = 10          # Cantidad de agujeros en Y
distancia_x = 15.0     # Distancia entre centros de agujeros en X (mm)
distancia_y = 15.0     # Distancia entre centros de agujeros en Y (mm)

# Configuración de los Orificios
diametro_orificio = 6.0    # Diámetro del agujero cilíndrico
radio_esfera_rebaje = 6.0  # Radio de la "esfera" imaginaria para el rebaje (debe ser mayor al radio del orificio)
profundidad_rebaje = 2.0   # Cuánto se hunde la esfera en la placa

# Configuración de la Placa y Marco
espesor_placa = 5.0    # Altura de la base donde van los agujeros
espesor_marco = 4.0    # Grosor de las paredes del marco
altura_marco = 12.0    # Altura total del marco (desde el suelo)
margen_interno = 5.0   # Espacio extra entre el último agujero y el marco

# --- 2. CÁLCULOS AUTOMÁTICOS DE DIMENSIONES ---

# Calculamos el tamaño total de la zona de agujeros
ancho_zona_agujeros = (num_columnas - 1) * distancia_x
alto_zona_agujeros = (num_filas - 1) * distancia_y

# Dimensiones totales de la placa (zona agujeros + margenes + espesor marco)
ancho_total = ancho_zona_agujeros + (2 * margen_interno) + (2 * espesor_marco)
largo_total = alto_zona_agujeros + (2 * margen_interno) + (2 * espesor_marco)

# --- 3. GENERACIÓN DEL MODELO ---

# A. Crear la base sólida (Placa base)
placa = cq.Workplane("XY").box(ancho_total, largo_total, espesor_placa)

# B. Generar la lista de coordenadas para la grilla
# Centramos la grilla restando la mitad del ancho/alto total de la zona de agujeros
puntos_grilla = []
inicio_x = -ancho_zona_agujeros / 2
inicio_y = -alto_zona_agujeros / 2

for i in range(num_columnas):
    for j in range(num_filas):
        x = inicio_x + (i * distancia_x)
        y = inicio_y + (j * distancia_y)
        puntos_grilla.append((x, y))

# C. Hacer los orificios cilíndricos y el rebaje esférico
# 1. Perforamos los cilindros pasantes
placa_perforada = (
    placa
    .faces(">Z") # Seleccionamos la cara superior
    .workplane()
    .pushPoints(puntos_grilla)
    .hole(diametro_orificio) # Solo .hole(), sin .cutBlind()
)

# 2. Hacemos el rebaje esférico
# Creamos una esfera herramienta para sustraer
esfera_herramienta = cq.Workplane("XY").sphere(radio_esfera_rebaje)

# Para cada punto, restamos la esfera en la posición correcta
# (Bajamos la esfera para que solo corte la parte superior)
posicion_z_esfera = (espesor_placa / 2) - profundidad_rebaje + radio_esfera_rebaje

for punto in puntos_grilla:
    # Movemos la esfera a la posición (X, Y) y la altura calculada
    corte = esfera_herramienta.translate((punto[0], punto[1], posicion_z_esfera))
    placa_perforada = placa_perforada.cut(corte)

# D. Crear el Marco
# Creamos un bloque del tamaño total y le restamos el interior
marco_exterior = cq.Workplane("XY").box(ancho_total, largo_total, altura_marco)
marco_interior = cq.Workplane("XY").box(
    ancho_total - (2 * espesor_marco),
    largo_total - (2 * espesor_marco),
    altura_marco
)
marco = marco_exterior.cut(marco_interior)

# Como el marco se crea centrado en Z=0 y la placa también, ajustamos alturas si es necesario
# En este caso, alineamos la base del marco con la base de la placa
# (CadQuery crea las cajas centradas en el origen por defecto)
diff_altura = (altura_marco - espesor_placa) / 2
marco = marco.translate((0, 0, diff_altura))

# --- 4. UNIÓN FINAL Y EXPORTACIÓN ---

resultado_final = placa_perforada.union(marco)

# Guardar como STL
nombre_archivo = f"placa_grilla_{num_columnas}x{num_filas}.stl"
cq.exporters.export(resultado_final, nombre_archivo)

print(f"¡Listo! Archivo generado: {nombre_archivo}")
print(f"Dimensiones: {ancho_total}mm x {largo_total}mm")