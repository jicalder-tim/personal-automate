import argparse
import csv
import json
import sys
from pathlib import Path


# --- PARTE 2: Combinar logs de GPS con nombres de vehículos ---
def combinar_logs_con_nombres(gpslogs_json_path, vehiculos_json_path, output_csv_path):
    try:
        print(f"Combinando logs de: {gpslogs_json_path}")
        print(f"Usando nombres de: {vehiculos_json_path}")

        # Cargar archivos JSON
        with open(gpslogs_json_path, "r", encoding="utf-8") as f:
            gpslogs_json = json.load(f)
        with open(vehiculos_json_path, "r", encoding="utf-8") as f:
            vehiculos_json = json.load(f)

        # Crear un diccionario id -> name
        id2name = {v["id"]: v["name"] for v in vehiculos_json}

        # Procesar logs
        registros = []
        for veh in gpslogs_json:
            veh_id = veh["id"]
            nombre = id2name.get(veh_id, f"id_{veh_id}")
            for log in veh["gps_logs"]:
                registro = {
                    "vehiculo_id": veh_id,
                    "vehiculo_nombre": nombre,
                    "t": log["t"],
                    "x": log["x"],
                    "y": log["y"],
                    "z": log["z"],
                    "speed": log["speed"],
                }
                registros.append(registro)

        # Escribir CSV
        campos = ["vehiculo_id", "vehiculo_nombre", "t", "x", "y", "z", "speed"]
        with open(output_csv_path, "w", newline="", encoding="utf-8") as fout:
            writer = csv.DictWriter(fout, fieldnames=campos)
            writer.writeheader()
            for reg in registros:
                writer.writerow(reg)

        print(f"Exportado correctamente a: {output_csv_path}")
        print(f"Total registros: {len(registros)}")

    except FileNotFoundError as e:
        print(f"Error: No se encontró el archivo: {e.filename}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error al leer JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error inesperado: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Herramienta para combinar logs de GPS con nombres de palas."
    )
    parser.add_argument("gpslogs", help="Archivo JSON con logs de GPS")
    parser.add_argument("shovels", help="Archivo JSON con metadatos de palas (nombres)")
    parser.add_argument("-o", "--output", help="Archivo CSV de salida")

    args = parser.parse_args()

    gps_path = Path(args.gpslogs)
    shovels_path = Path(args.shovels)

    if args.output:
        output_path = Path(args.output)
    else:
        # Nombre por defecto basado en el log de GPS
        output_path = gps_path.with_suffix(".csv")

    combinar_logs_con_nombres(gps_path, shovels_path, output_path)


if __name__ == "__main__":
    main()
