import csv
from datetime import datetime

input_file = "D:/Trabajo/Biopixel/Arduino/Atmos/AtmosDB_02.csv"  # Cambia esto por el nombre de tu archivo de entrada
output_file = "D:/Trabajo/Biopixel/Arduino/Atmos/AtmosDB_02_clean.csv"

def procesar_csv(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = ['timestamp', 'temp', 'relative_humidity']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            # Unir date y hour y convertir a timestamp ISO
            fecha = row['date']
            hora = row['hour']
            dt = datetime.strptime(f'{fecha} {hora}', '%d/%m/%Y %H:%M:%S')
            timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
            # Convertir valores decimales con coma a punto
            temp = row['temp'].replace(',', '.')
            rh = row['relative_humidity'].replace(',', '.')
            writer.writerow({'timestamp': timestamp, 'temp': temp, 'relative_humidity': rh})

if __name__ == '__main__':
    procesar_csv(input_file, output_file)

