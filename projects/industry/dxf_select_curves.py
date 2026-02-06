import ezdxf
import os


def filtrar_curvas_dxf(archivo_entrada, archivo_salida):
    try:
        print(f"Leyendo archivo: {archivo_entrada}...")

        # 1. Cargar el DXF
        doc = ezdxf.readfile(archivo_entrada)
        msp = doc.modelspace()

        # 2. Definir qué considera Rhino como "Curva" (Lista blanca)
        # Estos son los tipos de entidades DXF que queremos CONSERVAR.
        tipos_curva = {
            'LINE',  # Líneas simples
            'LWPOLYLINE',  # Polilíneas 2D (las más comunes)
            'POLYLINE',  # Polilíneas 2D antiguas o 3D
            'CIRCLE',  # Círculos
            'ARC',  # Arcos
            'ELLIPSE',  # Elipses
            'SPLINE',  # Curvas libres
            'HELIX'  # Hélices
        }

        # Contadores para el reporte
        total_elementos = 0
        elementos_borrados = 0

        # 3. Recolectar entidades que NO son curvas para borrarlas
        # (Es mejor recolectar primero y borrar después para no romper el iterador)
        entidades_a_borrar = []

        for entidad in msp:
            total_elementos += 1
            tipo = entidad.dxftype()

            # Si el tipo de entidad NO está en nuestra lista de curvas, lo marcamos para borrar.
            # Aquí es donde caen los 'HATCH' (Tramas), 'TEXT', 'MTEXT', 'DIMENSION', etc.
            if tipo not in tipos_curva:
                entidades_a_borrar.append(entidad)

        # 4. Ejecutar el borrado
        for entidad in entidades_a_borrar:
            msp.delete_entity(entidad)
            elementos_borrados += 1

        # 5. Guardar el nuevo archivo
        doc.saveas(archivo_salida)

        print("-" * 30)
        print(f"Proceso completado.")
        print(f"Total elementos procesados: {total_elementos}")
        print(f"Elementos eliminados (Tramas/Textos/Etc): {elementos_borrados}")
        print(f"Curvas conservadas: {total_elementos - elementos_borrados}")
        print(f"Archivo guardado en: {archivo_salida}")

    except IOError:
        print(f"Error: No se pudo abrir el archivo {archivo_entrada}. Verifica la ruta.")
    except ezdxf.DXFStructureError:
        print("Error: El archivo DXF está dañado o es inválido.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")


# --- Ejecución ---
if __name__ == "__main__":
    # Cambia estos nombres por tus archivos reales
    input_dxf = "D:\Trabajo\TiMining\Geometrico\Cerrejon\Planes\Semana 46\MSK_CERREJON_NOV13_19.dxf"
    output_dxf = "D:\Trabajo\TiMining\Geometrico\Cerrejon\Planes\Semana 46\MSK_CERREJON_NOV13_19_fix.dxf"

    # Verificamos si existe el archivo antes de correr
    if os.path.exists(input_dxf):
        filtrar_curvas_dxf(input_dxf, output_dxf)
    else:
        print(f"Por favor coloca un archivo llamado '{input_dxf}' en la carpeta o edita el script.")