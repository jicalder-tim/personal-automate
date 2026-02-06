import trimesh
import os

# 1. Definimos la ruta manualmente (usa la 'r' para evitar errores de barras)
ruta_archivo = r"D:\Trabajo\TiMining\Geometrico\Specialist\Vehiculos 3D IA\truck.glb"

if os.path.exists(ruta_archivo):
    print(f"Cargando archivo: {ruta_archivo}")
    # 2. Carga el archivo .glb
    scene = trimesh.load(ruta_archivo)

    # 3. Exporta como .obj
    ruta_salida = ruta_archivo.replace('.glb', '.obj')
    scene.export(ruta_salida)

    print(f"¡Conversión completada! Archivo generado en: {ruta_salida}")
else:
    print("Error: No se encontró el archivo .glb en la ruta especificada.")