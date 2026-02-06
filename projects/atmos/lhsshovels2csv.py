import csv
import json
from datetime import datetime
import sys

# --- PARTE 1: Procesar CSV de clima ---
def procesar_csv_ambiente(input_csv, output_csv):
    with open(input_csv, 'r', encoding='utf-8') as fin, open(output_csv, 'w', newline='', encoding='utf-8') as fout:
        reader = csv.DictReader(fin)
        fieldnames = ['timestamp', 'temp', 'relative_humidity']
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            # Combinar fecha y hora en un timestamp
            dt_str = f"{row['date']} {row['hour']}"
            dt = datetime.strptime(dt_str, '%d/%m/%Y %H:%M:%S')
            timestamp = dt.isoformat(sep=' ')
            # Convertir valores numéricos con coma a punto
            temp = row['temp'].replace(',', '.')
            rh = row['relative_humidity'].replace(',', '.')
            writer.writerow({'timestamp': timestamp, 'temp': temp, 'relative_humidity': rh})

# --- PARTE 2: Combinar logs de GPS con nombres de vehículos ---
def combinar_logs_con_nombres(gpslogs_json, vehiculos_json, output_csv):
    # Si se pasan rutas, cargar los archivos JSON
    if isinstance(gpslogs_json, str):
        with open(gpslogs_json, 'r', encoding='utf-8') as f:
            gpslogs_json = json.load(f)
    if isinstance(vehiculos_json, str):
        with open(vehiculos_json, 'r', encoding='utf-8') as f:
            vehiculos_json = json.load(f)
    # Crear un diccionario id -> name
    id2name = {v['id']: v['name'] for v in vehiculos_json}
    # Procesar logs
    registros = []
    for veh in gpslogs_json:
        veh_id = veh['id']
        nombre = id2name.get(veh_id, f'id_{veh_id}')
        for log in veh['gps_logs']:
            registro = {
                'vehiculo_id': veh_id,
                'vehiculo_nombre': nombre,
                't': log['t'],
                'x': log['x'],
                'y': log['y'],
                'z': log['z'],
                'speed': log['speed']
            }
            registros.append(registro)
    # Escribir CSV
    campos = ['vehiculo_id', 'vehiculo_nombre', 't', 'x', 'y', 'z', 'speed']
    with open(output_csv, 'w', newline='', encoding='utf-8') as fout:
        writer = csv.DictWriter(fout, fieldnames=campos)
        writer.writeheader()
        for reg in registros:
            writer.writerow(reg)

# --- USO EJEMPLO ---
if __name__ == '__main__':
    # Ejemplo de uso:
    # procesar_csv_ambiente('input.csv', 'output.csv')
    combinar_logs_con_nombres("D:/Trabajo/TiMining/Geometrico/MLP/GPS Palas/gpslogs010126_21PMChile-030126_1130AMChile.json", "D:/Trabajo/TiMining/Geometrico/MLP/GPS Palas/shovels 3.json", "D:/Trabajo/TiMining/Geometrico/MLP/GPS Palas/logs_shovels_010126_030126.csv")
    pass
