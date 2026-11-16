"""Genera datos SINTÉTICOS (no reales) para probar el pipeline sin descargar nada.

    python data/sample/generar_muestra.py
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
ORGANISMOS = [("69.000.001-1", "Municipalidad Ejemplo Norte"), ("69.000.002-2", "Municipalidad Ejemplo Sur"),
              ("69.000.003-3", "Servicio de Salud Ejemplo"), ("69.000.004-4", "Liceo Ejemplo")]
PROVEEDORES = [(f"76.{100 + i}.000-{i % 10}", f"Proveedor Ficticio {i:02d} SpA") for i in range(1, 13)]
RUBROS = ["Alimentos", "Aseo", "Computación", "Construcción", "Servicios profesionales"]
MODALIDADES = ["Licitación Pública", "Convenio Marco", "Compra Ágil", "Trato Directo"]

filas = []
for i in range(1, 301):
    org = random.choice(ORGANISMOS)
    prov = PROVEEDORES[min(int(random.expovariate(0.35)), len(PROVEEDORES) - 1)]  # pocos concentran
    envio = date(2025, 1, 1) + timedelta(days=random.randint(0, 180))
    acepta = envio + timedelta(days=random.randint(0, 6)) if random.random() < 0.9 else None
    monto = int(random.lognormvariate(13, 1.1))
    monto_txt = f"{monto:,}".replace(",", ".") if i % 3 == 0 else str(monto)   # mezcla de formatos
    fecha_txt = envio.strftime("%d-%m-%Y") if i % 10 == 0 else envio.isoformat()
    if i in (7, 8):
        fecha_txt = "sin dato"                                               # 2 fechas inválidas
    filas.append([f"SIM-{i:05d}", "Aceptada", fecha_txt, acepta.isoformat() if acepta else "",
                  random.choice(MODALIDADES), org[1], org[0], prov[1], prov[0],
                  random.choice(RUBROS), monto_txt])
filas.append(filas[10][:])   # un duplicado exacto

destino = Path(__file__).parent / "ordenes_muestra.csv"
with open(destino, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["Codigo", "Estado", "FechaEnvio", "FechaAceptacion", "Tipo", "NombreOrganismo",
                "RutOrganismo", "NombreProveedor", "RutProveedor", "Rubro", "MontoTotal"])
    w.writerows(filas)
print(f"Escribí {len(filas)} filas en {destino}")
