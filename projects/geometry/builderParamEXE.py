import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cadquery as cq
import math


# --- FUNCIONES DE SEGURIDAD ---
def safe_union(obj_base, obj_add):
    try:
        if obj_add.vals(): return obj_base.union(obj_add)
    except:
        pass
    return obj_base


def safe_cut(obj_base, obj_sub):
    try:
        if obj_sub.vals(): return obj_base.cut(obj_sub)
    except:
        pass
    return obj_base


# --- GENERADOR DE RIELES (CORRECCIÓN TRIGONOMÉTRICA) ---
def crear_riel_trigonometrico(largo_costura, h_proyeccion, w_base, angulo_grados, orientacion, tipo, tolerancia):
    """
    Crea un riel con compensación geométrica exacta para el ángulo.
    """

    # Constantes de Ingeniería
    ANCHOR_DEPTH = 2.0  # Anclaje del macho
    BUFFER_CORTE = 10.0  # Exceso de largo para la hembra

    # Conversión a radianes
    rads = math.radians(angulo_grados)
    sin_a = math.sin(rads)
    tan_a = math.tan(rads)

    # Evitar división por cero en ángulos rectos
    if angulo_grados >= 89.9:
        tan_a = 999999.0
        sin_a = 1.0

    # --- CÁLCULO DE DIMENSIONES ---

    if tipo == 'MACHO':
        # El macho respeta las medidas nominales
        h_final = h_proyeccion
        w_b_final = w_base

        # Calculamos el ancho en la punta (w_top) basado en el ángulo y altura
        # Delta es lo que crece hacia un lado
        delta_one_side = h_final / tan_a
        w_t_final = w_base + (2 * delta_one_side)

        # Posición Z (profundidad)
        z_start = -ANCHOR_DEPTH
        largo_final = largo_costura

    else:  # HEMBRA (CORTADOR)
        # Aquí aplicamos la corrección de tolerancia
        # 1. Desplazamiento horizontal necesario para lograr el gap perpendicular
        expansion_x = tolerancia / sin_a

        # 2. La base se ensancha
        w_b_final = w_base + (2 * expansion_x)

        # 3. La altura (profundidad del corte) aumenta para dejar aire en la punta
        # Sumamos tolerancia vertical para que la punta del macho no toque el fondo
        h_final = h_proyeccion + tolerancia

        # 4. Calculamos el nuevo ancho en la punta (w_top)
        # Usamos la nueva altura y el nuevo ancho base para proyectar el mismo ángulo
        delta_one_side = h_final / tan_a
        w_t_final = w_b_final + (2 * delta_one_side)

        # Posición Z
        z_start = 0
        largo_final = largo_costura + BUFFER_CORTE

    # --- GENERACIÓN DE PUNTOS ---
    # Perfil 2D: (Coordenada Proyección, Coordenada Ancho)
    # P1(Base) -> P2(Punta) -> P3(Punta) -> P4(Base)

    pts = [
        (z_start, -w_b_final / 2.0),
        (h_final, -w_t_final / 2.0),
        (h_final, w_t_final / 2.0),
        (z_start, w_b_final / 2.0)
    ]

    # --- EXTRUSIÓN ---
    if orientacion == 'VERTICAL_Y':
        # Riel corre en Y. Diente apunta en X. Perfil en plano XZ.
        wire = cq.Workplane("XZ").polyline(pts).close()
        riel = wire.extrude(largo_final / 2.0, both=True)

    elif orientacion == 'HORIZONTAL_X':
        # Riel corre en X. Diente apunta en Y. Perfil en plano YZ.
        wire = cq.Workplane("YZ").polyline(pts).close()
        riel = wire.extrude(largo_final / 2.0, both=True)

    return riel


def generar_stl():
    try:
        # --- 1. PARAMETROS ---
        num_cols = int(entry_num_columnas.get())
        num_filas = int(entry_num_filas.get())
        dist_x = float(entry_distancia_x.get())
        dist_y = float(entry_distancia_y.get())
        diametro = float(entry_diametro.get())
        r_rebaje = float(entry_radio_rebaje.get())
        d_rebaje = float(entry_prof_rebaje.get())
        e_placa = float(entry_espesor_placa.get())
        e_marco = float(entry_espesor_marco.get())
        h_marco = float(entry_altura_marco.get())
        dividir = var_dividir.get()
        usar_rieles = var_rieles.get()
        tol = float(entry_tolerancia.get())

        # Rieles
        RIEL_PROYECCION = float(entry_riel_proyeccion.get())
        RIEL_ANCHO_BASE = float(entry_riel_ancho.get())
        RIEL_ANGULO = float(entry_riel_angulo.get())

        GAP_CENTRAL = 15.0

        # --- 2. BASE ---
        ancho_zona = (num_cols - 1) * dist_x
        alto_zona = (num_filas - 1) * dist_y
        ancho_int = ancho_zona + dist_x
        largo_int = alto_zona + dist_y
        ancho_tot = ancho_int + (2 * e_marco)
        largo_tot = largo_int + (2 * e_marco)

        root.title("Generando Placa...")
        root.update()

        placa = cq.Workplane("XY").box(ancho_tot, largo_tot, e_placa)
        pts = []
        ini_x, ini_y = -ancho_zona / 2, -alto_zona / 2
        for i in range(num_cols):
            for j in range(num_filas):
                pts.append((ini_x + i * dist_x, ini_y + j * dist_y))

        placa = placa.faces(">Z").workplane().pushPoints(pts).hole(diametro)

        esfera = cq.Workplane("XY").sphere(r_rebaje)
        z_esfera = (e_placa / 2) - d_rebaje + r_rebaje

        root.title("Procesando rebajes...")
        root.update()
        for i, pt in enumerate(pts):
            placa = placa.cut(esfera.translate((pt[0], pt[1], z_esfera)))
            if i % 20 == 0: root.update()

        marco = cq.Workplane("XY").box(ancho_tot, largo_tot, h_marco)
        marco = marco.cut(cq.Workplane("XY").box(ancho_int, largo_int, h_marco))
        marco = marco.translate((0, 0, (h_marco - e_placa) / 2))

        modelo = placa.union(marco)

        if not dividir:
            filepath = filedialog.asksaveasfilename(defaultextension=".stl", filetypes=[("STL", "*.stl")])
            if filepath: cq.exporters.export(modelo, filepath)
            return

        # --- 3. DIVISIÓN ---
        root.title("Dividiendo...")
        root.update()

        s = max(ancho_tot, largo_tot) * 2.0

        box_A = cq.Workplane("XY").box(s, s, s).translate((-s / 2, s / 2, 0))  # Top-Left
        box_B = cq.Workplane("XY").box(s, s, s).translate((s / 2, s / 2, 0))  # Top-Right
        box_C = cq.Workplane("XY").box(s, s, s).translate((-s / 2, -s / 2, 0))  # Bot-Left
        box_D = cq.Workplane("XY").box(s, s, s).translate((s / 2, -s / 2, 0))  # Bot-Right

        base_A = modelo.intersect(box_A)
        base_B = modelo.intersect(box_B)
        base_C = modelo.intersect(box_C)
        base_D = modelo.intersect(box_D)

        if not usar_rieles:
            cq.exporters.export(base_A, "1_A.stl");
            cq.exporters.export(base_B, "2_B.stl")
            cq.exporters.export(base_C, "3_C.stl");
            cq.exporters.export(base_D, "4_D.stl")
            return

        # --- 4. RIELES CON CORRECCIÓN TRIGONOMÉTRICA ---
        root.title("Calculando geometría exacta...")

        cuadrante_Y = largo_tot / 2.0
        cuadrante_X = ancho_tot / 2.0

        len_macho_vert = cuadrante_Y - GAP_CENTRAL
        len_hembra_vert = cuadrante_Y
        len_macho_horiz = cuadrante_X - GAP_CENTRAL
        len_hembra_horiz = cuadrante_X

        # === A. RIELES VERTICALES ===

        # Superior (Para A y B)
        rv_macho_sup = crear_riel_trigonometrico(len_macho_vert, RIEL_PROYECCION, RIEL_ANCHO_BASE, RIEL_ANGULO,
                                                 'VERTICAL_Y', 'MACHO', tol)
        y_center_sup_macho = (cuadrante_Y + GAP_CENTRAL) / 2.0
        rv_macho_sup = rv_macho_sup.translate((0, y_center_sup_macho, 0))

        rv_hembra_sup = crear_riel_trigonometrico(len_hembra_vert, RIEL_PROYECCION, RIEL_ANCHO_BASE, RIEL_ANGULO,
                                                  'VERTICAL_Y', 'HEMBRA', tol)
        rv_hembra_sup = rv_hembra_sup.translate((0, cuadrante_Y / 2.0, 0))

        # Inferior (Para C y D)
        rv_macho_inf = crear_riel_trigonometrico(len_macho_vert, RIEL_PROYECCION, RIEL_ANCHO_BASE, RIEL_ANGULO,
                                                 'VERTICAL_Y', 'MACHO', tol)
        y_center_inf_macho = -(cuadrante_Y + GAP_CENTRAL) / 2.0
        rv_macho_inf = rv_macho_inf.translate((0, y_center_inf_macho, 0))

        rv_hembra_inf = crear_riel_trigonometrico(len_hembra_vert, RIEL_PROYECCION, RIEL_ANCHO_BASE, RIEL_ANGULO,
                                                  'VERTICAL_Y', 'HEMBRA', tol)
        rv_hembra_inf = rv_hembra_inf.translate((0, -cuadrante_Y / 2.0, 0))

        # === B. RIELES HORIZONTALES ===

        # Izquierdo (Para C y A)
        rh_macho_izq = crear_riel_trigonometrico(len_macho_horiz, RIEL_PROYECCION, RIEL_ANCHO_BASE, RIEL_ANGULO,
                                                 'HORIZONTAL_X', 'MACHO', tol)
        x_center_macho_izq = -(cuadrante_X + GAP_CENTRAL) / 2.0
        rh_macho_izq = rh_macho_izq.translate((x_center_macho_izq, 0, 0))

        rh_hembra_izq = crear_riel_trigonometrico(len_hembra_horiz, RIEL_PROYECCION, RIEL_ANCHO_BASE, RIEL_ANGULO,
                                                  'HORIZONTAL_X', 'HEMBRA', tol)
        rh_hembra_izq = rh_hembra_izq.translate((-cuadrante_X / 2.0, 0, 0))

        # Derecho (Para D y B)
        rh_macho_der = crear_riel_trigonometrico(len_macho_horiz, RIEL_PROYECCION, RIEL_ANCHO_BASE, RIEL_ANGULO,
                                                 'HORIZONTAL_X', 'MACHO', tol)
        x_center_macho_der = (cuadrante_X + GAP_CENTRAL) / 2.0
        rh_macho_der = rh_macho_der.translate((x_center_macho_der, 0, 0))

        rh_hembra_der = crear_riel_trigonometrico(len_hembra_horiz, RIEL_PROYECCION, RIEL_ANCHO_BASE, RIEL_ANGULO,
                                                  'HORIZONTAL_X', 'HEMBRA', tol)
        rh_hembra_der = rh_hembra_der.translate((cuadrante_X / 2.0, 0, 0))

        # --- 5. ENSAMBLAJE FINAL ---

        # A: Macho a Der, Hembra Abajo
        final_A = safe_union(base_A, rv_macho_sup)
        final_A = safe_cut(final_A, rh_hembra_izq)

        # B: Hembra a Izq, Hembra Abajo
        final_B = safe_cut(base_B, rv_hembra_sup)
        final_B = safe_cut(final_B, rh_hembra_der)

        # C: Macho a Der, Macho Arriba
        final_C = safe_union(base_C, rv_macho_inf)
        final_C = safe_union(final_C, rh_macho_izq)

        # D: Hembra a Izq, Macho Arriba
        final_D = safe_cut(base_D, rv_hembra_inf)
        final_D = safe_union(final_D, rh_macho_der)

        directory = filedialog.askdirectory()
        if directory:
            cq.exporters.export(final_A, f"{directory}/1_A_SupIzq.stl")
            cq.exporters.export(final_B, f"{directory}/2_B_SupDer.stl")
            cq.exporters.export(final_C, f"{directory}/3_C_InfIzq.stl")
            cq.exporters.export(final_D, f"{directory}/4_D_InfDer.stl")
            messagebox.showinfo("Éxito", f"Archivos generados en: {directory}")

    except Exception as e:
        messagebox.showerror("Error", str(e))
        print(e)


# --- GUI ---
root = tk.Tk()
root.title("PlateBuilder - Trig Precision V6")
main = ttk.Frame(root, padding=20)
main.pack()


def inp(txt, r, val):
    ttk.Label(main, text=txt).grid(column=0, row=r, sticky="w")
    e = ttk.Entry(main);
    e.insert(0, val);
    e.grid(column=1, row=r)
    return e


entry_num_columnas = inp("Columnas:", 0, 10)
entry_num_filas = inp("Filas:", 1, 10)
entry_distancia_x = inp("Dist X:", 2, 35)
entry_distancia_y = inp("Dist Y:", 3, 35)
entry_diametro = inp("Diametro Agujero:", 4, 6)
entry_radio_rebaje = inp("Radio Rebaje:", 5, 10)
entry_prof_rebaje = inp("Prof Rebaje:", 6, 4)
entry_espesor_placa = inp("Esp Placa:", 7, 15)
entry_espesor_marco = inp("Esp Marco:", 8, 4)
entry_altura_marco = inp("Alt Marco:", 9, 50)
ttk.Label(main, text="--- Rieles ---").grid(column=0, row=10, columnspan=2)
entry_riel_proyeccion = inp("Proyección (Largo Diente):", 11, 8.0)
entry_riel_ancho = inp("Ancho Base Riel:", 12, 6.0)
entry_riel_angulo = inp("Ángulo Cono (grados):", 13, 60.0)
entry_tolerancia = inp("Tolerancia (Gap):", 14, 0.2)
var_dividir = tk.BooleanVar(value=True);
ttk.Checkbutton(main, text="Dividir", variable=var_dividir).grid(column=0, row=15)
var_rieles = tk.BooleanVar(value=True);
ttk.Checkbutton(main, text="Generar Rieles", variable=var_rieles).grid(column=0, row=16)
ttk.Button(main, text="GENERAR", command=generar_stl).grid(column=0, row=17, columnspan=2, pady=15)

root.mainloop()