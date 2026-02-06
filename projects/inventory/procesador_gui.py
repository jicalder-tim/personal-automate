import pandas as pd
import csv
import io
import os  # Necesario para manejar nombres y rutas de archivos
import tkinter as tk  # Para la interfaz gráfica
from tkinter import filedialog, messagebox  # Para los diálogos de "abrir archivo" y "mensajes"


# ===================================================================
# PASO 1: NUESTRA FUNCIÓN DE PROCESAMIENTO (YA CORREGIDA)
# ===================================================================
def procesar_reporte_inventario(contenido_archivo):
    """
    Procesa el contenido de un reporte de inventario en formato de texto
    y lo convierte en un DataFrame de Pandas.
    (Versión corregida para alinear columnas)
    """

    # 1. Definición de Columnas
    nombres_columnas_datos = [
        "Nombre Materia Prima", "IdArt", "UnidInv", "InvInic", "UnidComp", "InvFinal",
        "CostxUnid", "TotalFinal", "Días a la Mano",
        "UsoUnid_Real", "UsoUnid_Teórico", "UsoUnid_Variación",
        "ValorUso_Real", "ValorUso_Teórico", "ValorUso_Variación",
        "PorcUso_Real", "PorcUso_Teórico", "PorcUso_Variación"
    ]

    columnas_finales = ["Categoria", "Subcategoria"] + nombres_columnas_datos

    # 2. Inicialización de variables
    datos_procesados = []
    categoria_actual = None
    subcategoria_actual = None

    lineas = contenido_archivo.splitlines()

    # 3. Iteración línea por línea
    for linea in lineas:
        linea = linea.strip()

        # --- REGLAS DE OMISIÓN (JUNK) ---
        if (not linea or
                linea.startswith("Copyright") or
                linea.startswith("*El Cálculo") or
                linea.startswith("Theoretical") or
                linea.startswith("V 21.1.158.0") or
                "3243.CEC .LaFlorida" in linea or
                linea.startswith("UsoenUnid,Valor $ Uso") or
                linea.startswith("Nombre Materia Prima") or
                linea.startswith("IdArt,UnidInv") or
                linea.startswith("VentasNetas:")
        ):
            continue

        # --- REGLAS DE ESTADO (CATEGORÍAS) ---
        if linea.startswith("Total:"):
            if linea.startswith("Total:,") and "," in linea:
                partes = linea.split(',')
                if len(partes) > 1:
                    nombre_total = partes[1].strip()
                    if nombre_total == subcategoria_actual:
                        subcategoria_actual = None
                    elif nombre_total == categoria_actual:
                        categoria_actual = None
                        subcategoria_actual = None
            continue

        if (linea.isupper() and
                ',' not in linea and
                '$' not in linea and
                not any(c.isdigit() for c in linea)):

            if categoria_actual is None:
                categoria_actual = linea
            elif subcategoria_actual is None or subcategoria_actual == categoria_actual:
                subcategoria_actual = linea
            else:
                if categoria_actual == subcategoria_actual:
                    categoria_actual = linea
                    subcategoria_actual = None
                else:
                    subcategoria_actual = linea
            continue

        # --- PROCESAMIENTO DE DATOS ---
        try:
            f = io.StringIO(linea)
            reader = csv.reader(f)
            campos = next(reader)

            if len(campos) == 20:
                # Tomamos campos 0-3
                # Saltamos campo 4 (columna vacía de UnidComp)
                # Tomamos campos 5-6 (datos de UnidComp e InvFinal)
                # Saltamos campo 7 (columna vacía)
                # Tomamos campos 8-19 (el resto de los datos)
                fila_datos = campos[0:4] + campos[5:7] + campos[8:20]

                fila_completa = [categoria_actual, subcategoria_actual] + fila_datos
                datos_procesados.append(fila_completa)
        except Exception:
            continue

    # 4. Creación del DataFrame
    print(f"Procesamiento finalizado. Se encontraron {len(datos_procesados)} registros.")

    if not datos_procesados:
        print("No se encontraron datos para crear el DataFrame.")
        return pd.DataFrame(columns=columnas_finales)

    df = pd.DataFrame(datos_procesados, columns=columnas_finales)
    return df


# ===================================================================
# PASO 2: LA NUEVA FUNCIÓN PRINCIPAL CON INTERFAZ GRÁFICA
# ===================================================================
def ejecutar_procesador():
    """
    Función principal que usa Tkinter para:
    1. Pedir el archivo TXT.
    2. Generar el nombre del archivo CSV de salida.
    3. Leer, procesar y guardar el archivo.
    4. Mostrar mensajes de éxito o error.
    """

    # Oculta la ventana principal de Tkinter (solo queremos el diálogo)
    root = tk.Tk()
    root.withdraw()

    print("Mostrando diálogo para seleccionar archivo TXT...")

    # Abrir la ventana de "Abrir Archivo"
    filepath = filedialog.askopenfilename(
        title="Selecciona el archivo TXT de inventario",
        filetypes=[("Archivos de Texto", "*.txt"), ("Todos los archivos", "*.*")]
    )

    # Si el usuario cancela, filepath estará vacío
    if not filepath:
        messagebox.showinfo("Cancelado", "No se seleccionó ningún archivo.")
        print("Operación cancelada por el usuario.")
        root.destroy()
        return

    print(f"Archivo seleccionado: {filepath}")

    # Bloque try-except para manejar cualquier error durante el proceso
    try:
        # --- Generar el nombre del archivo de salida ---
        # 1. Obtiene el directorio (ej: "C:/Mis Documentos")
        directorio = os.path.dirname(filepath)
        # 2. Obtiene el nombre base (ej: "Inventario.txt")
        nombre_base = os.path.basename(filepath)
        # 3. Obtiene el nombre sin extensión (ej: "Inventario")
        nombre_sin_ext = os.path.splitext(nombre_base)[0]

        # 4. Crea el nombre del CSV (ej: "Inventario.csv")
        nombre_csv_salida = nombre_sin_ext + ".csv"
        # 5. Crea la ruta completa de salida (ej: "C:/Mis Documentos/Inventario.csv")
        output_path = os.path.join(directorio, nombre_csv_salida)

        # --- Leer el archivo de entrada ---
        print("Leyendo archivo...")
        with open(filepath, 'r', encoding='utf-16-le') as f:
            contenido_completo = f.read()

        # --- Procesar usando nuestra función ---
        print("Procesando datos...")
        df_resultado = procesar_reporte_inventario(contenido_completo)

        if df_resultado.empty:
            raise Exception("No se encontraron datos válidos para procesar en el archivo.")

        # --- Guardar el CSV ---
        print(f"Guardando CSV en: {output_path}")
        df_resultado.to_csv(output_path, index=False, encoding='utf-8-sig')

        # --- Mostrar mensaje de éxito ---
        messagebox.showinfo(
            "Éxito",
            f"¡Proceso completado!\n\nEl archivo se ha guardado como:\n{nombre_csv_salida}"
        )

    except Exception as e:
        # --- Mostrar mensaje de error ---
        print(f"¡ERROR! {e}")
        messagebox.showerror(
            "Error",
            f"Ocurrió un error inesperado durante el procesamiento:\n\n{e}"
        )

    finally:
        # Asegurarse de que la ventana de Tkinter se cierre
        root.destroy()


# ===================================================================
# PASO 3: EL PUNTO DE ENTRADA
# ===================================================================
if __name__ == "__main__":
    # Cuando el script se ejecute, llamará a la función de la GUI
    ejecutar_procesador()