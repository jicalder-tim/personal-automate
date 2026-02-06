import cv2
import mediapipe as mp
import numpy as np
import time
import pyautogui

# --- ESTÉTICA DE MARCA (Colores Neon) ---
C_UI = (255, 191, 0)  # Cian Eléctrico
C_ACCENT = (0, 255, 127)  # Verde Primavera
C_ALERT = (0, 0, 255)  # Rojo Alerta
ALPHA = 0.6  # Transparencia de la UI


class AuraUI:
    def __init__(self):
        self.mp_face = mp.solutions.face_mesh
        self.face_mesh = self.mp_face.FaceMesh(refine_landmarks=True)
        self.hands = mp.solutions.hands.Hands(min_detection_confidence=0.8)

        # Variables de estado
        self.volume_level = 50
        self.is_pinching = False
        self.posture_warning = False

        # Filtros
        self.smooth_pitch = 0

    def draw_glass_panel(self, img, x, y, w, h, label, value):
        """Dibuja un panel con efecto de cristal esmerilado."""
        overlay = img.copy()
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (50, 50, 50), -1)
        cv2.addWeighted(overlay, ALPHA, img, 1 - ALPHA, 0, img)
        cv2.rectangle(img, (x, y), (x + w, y + h), C_UI, 1)

        # Texto
        cv2.putText(img, label, (x + 10, y + 25), 0, 0.6, (255, 255, 255), 1)
        # Barra de progreso
        bar_w = int((value / 100) * (w - 20))
        cv2.rectangle(img, (x + 10, y + 40), (x + w - 10, y + 55), (100, 100, 100), -1)
        cv2.rectangle(img, (x + 10, y + 40), (x + 10 + bar_w, y + 55), C_ACCENT, -1)

    def run(self):
        cap = cv2.VideoCapture(0)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Procesar IA
            face_res = self.face_mesh.process(rgb)
            hand_res = self.hands.process(rgb)

            # 1. ANALISIS DE POSTURA (Head Pose Simplificado)
            if face_res.multi_face_landmarks:
                lms = face_res.multi_face_landmarks[0].landmark
                # Diferencia entre frente (10) y barbilla (152) para detectar inclinación
                pitch = (lms[10].y - lms[152].y)
                self.smooth_pitch = 0.1 * pitch + 0.9 * self.smooth_pitch

                # Si la cabeza baja mucho (smooth_pitch > umbral), alerta
                self.posture_warning = self.smooth_pitch > -0.25  # Ajuste según cámara

                # HUD Dinámico (Sigue a la nariz)
                nx, ny = int(lms[1].x * w), int(lms[1].y * h)
                cv2.circle(frame, (nx, ny), 40, C_UI, 1)
                cv2.line(frame, (nx - 50, ny), (nx + 50, ny), C_UI, 1)

            # 2. CONTROL GESTUAL (Mano)
            if hand_res.multi_hand_landmarks:
                hlm = hand_res.multi_hand_landmarks[0].landmark
                px, py = int(hlm[8].x * w), int(hlm[8].y * h)  # Punta índice

                # Gesto de Pinza (Pinch)
                dist = np.sqrt((hlm[4].x - hlm[8].x) ** 2 + (hlm[4].y - hlm[8].y) ** 2)
                self.is_pinching = dist < 0.05

                if self.is_pinching:
                    # Mapear altura de la mano a nivel de volumen
                    self.volume_level = np.clip(int((1 - hlm[8].y) * 100), 0, 100)
                    cv2.circle(frame, (px, py), 15, C_ACCENT, -1)
                    # Actualizar volumen del sistema real (Windows)
                    # pyautogui.press('volumeup' if self.volume_level > 50 else 'volumedown')
                else:
                    cv2.circle(frame, (px, py), 10, C_UI, 2)

            # 3. RENDERIZADO DE INTERFAZ "PRODUCTO"
            # Panel de Control
            self.draw_glass_panel(frame, 30, 30, 200, 80, "AUDIO SPATIAL", self.volume_level)

            # Alerta de Salud
            if self.posture_warning:
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, 0), (w, h), C_ALERT, -1)
                cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
                cv2.putText(frame, "MEJORA TU POSTURA", (w // 2 - 100, h - 50), 0, 0.8, (255, 255, 255), 2)

            # Estética Cyberpunk (Esquinas)
            cv2.putText(frame, "AURA OS v1.0", (w - 150, 30), 0, 0.5, C_UI, 1)

            cv2.imshow("Aura Spatial Controller", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break

        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    app = AuraUI()
    app.run()