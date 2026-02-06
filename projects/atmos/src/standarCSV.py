import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path


def procesar_csv(input_file, output_file):
    print(f"Procesando: {input_file} -> {output_file}")
    try:
        with (
            open(input_file, "r", encoding="utf-8") as infile,
            open(output_file, "w", newline="", encoding="utf-8") as outfile,
        ):
            reader = csv.DictReader(infile)
            fieldnames = ["timestamp", "temp", "relative_humidity"]
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            count = 0
            for row in reader:
                # Unir date y hour y convertir a timestamp ISO
                # Manejar formatos flexibles si es necesario
                try:
                    fecha = row["date"]
                    hora = row["hour"]
                    dt = datetime.strptime(f"{fecha} {hora}", "%d/%m/%Y %H:%M:%S")
                    timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")

                    # Convertir valores decimales con coma a punto
                    temp = row["temp"].replace(",", ".")
                    rh = row["relative_humidity"].replace(",", ".")

                    writer.writerow(
                        {"timestamp": timestamp, "temp": temp, "relative_humidity": rh}
                    )
                    count += 1
                except ValueError as e:
                    print(f"Error procesando fila {count + 1}: {e}")
                    continue
                except KeyError as e:
                    print(f"Error: Columna faltante en el CSV de entrada: {e}")
                    sys.exit(1)

            print(f"Completado. {count} registros procesados.")

    except FileNotFoundError:
        print(f"Error: El archivo de entrada '{input_file}' no existe.")
        sys.exit(1)
    except Exception as e:
        print(f"Error inesperado: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Limpiador y estandarizador de CSVs de Atmos."
    )
    parser.add_argument("input", help="Ruta del archivo CSV de entrada")
    parser.add_argument(
        "-o", "--output", help="Ruta del archivo CSV de salida (opcional)"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not args.output:
        # Generar nombre de salida automático: archivo_clean.csv
        output_path = input_path.with_stem(f"{input_path.stem}_clean")
    else:
        output_path = Path(args.output)

    procesar_csv(input_path, output_path)


if __name__ == "__main__":
    main()
