import os
import cv2
import numpy as np

# Ruta absoluta: desde src/utils sube a src y entra en assets
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Sube dos niveles hasta la raíz y entra en assets
DEFAULT_TEMPLATE_PATH = os.path.normpath(
    os.path.join(CURRENT_DIR, "..", "..", "assets", "template_spin_arrows.png")
)

def locate_spin_button(
    screenshot_path: str, 
    template_path: str = None, 
    threshold: float = 0.40
) -> tuple[int, int] | None:
    """
    Busca el icono de las flechas (Pragmatic Play) usando Template Matching multiescala.
    Sirve tanto para la pantalla de bienvenida como para el botón de tirar (Spin).
    
    Devuelve: (x, y) del centro del botón o None si no supera el umbral.
    """
    if template_path is None:
        template_path = DEFAULT_TEMPLATE_PATH

    if not os.path.exists(screenshot_path):
        print(f"[VISION ERROR] Captura no encontrada en: {screenshot_path}")
        return None
    if not os.path.exists(template_path):
        print(f"[VISION ERROR] Plantilla no encontrada en: {template_path}")
        return None

    img = cv2.imread(screenshot_path, cv2.IMREAD_GRAYSCALE)
    tpl = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

    if img is None or tpl is None:
        return None

    best_val = -1
    best_loc = None
    best_size = (0, 0)

    # Barrido en múltiples escalas para tolerar variaciones de zoom o resolución
    for scale in np.linspace(0.6, 1.4, 17):
        w = int(tpl.shape[1] * scale)
        h = int(tpl.shape[0] * scale)

        if w >= img.shape[1] or h >= img.shape[0] or w < 10 or h < 10:
            continue

        resized = cv2.resize(tpl, (w, h), interpolation=cv2.INTER_AREA)
        res = cv2.matchTemplate(img, resized, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        if max_val > best_val:
            best_val = max_val
            best_loc = max_loc
            best_size = (w, h)

    print(f"[DEBUG VISION] Coincidencia: {best_val * 100:.2f}% (Mínimo exigido: {threshold * 100:.2f}%)")

    if best_val >= threshold:
        center_x = best_loc[0] + best_size[0] // 2
        center_y = best_loc[1] + best_size[1] // 2
        return (center_x, center_y)

    return None

# Alias para compatibilidad con código existente
get_spin_coordinates = locate_spin_button


def verify_spin_movement(
    image_path_before: str, 
    image_path_after: str, 
    movement_threshold: int = 10000
) -> bool:
    """
    Compara dos fotogramas mediante resta absoluta para verificar si los carretes giraron.
    Si tienen tamaños diferentes, redimensiona automáticamente para evitar el error de OpenCV.
    """
    if not os.path.exists(image_path_before) or not os.path.exists(image_path_after):
        print("[VISION ERROR] Faltan capturas para verificar movimiento.")
        return False

    img_before = cv2.imread(image_path_before, cv2.IMREAD_GRAYSCALE)
    img_after = cv2.imread(image_path_after, cv2.IMREAD_GRAYSCALE)

    if img_before is not None and img_after is not None:
        # Asegurar idéntica resolución antes de restar matrices
        h, w = img_before.shape[:2]
        if img_after.shape[:2] != (h, w):
            img_after = cv2.resize(img_after, (w, h), interpolation=cv2.INTER_AREA)

        diff = cv2.absdiff(img_before, img_after)
        total_change = int(np.sum(diff))
        print(f"[DEBUG VISION] Magnitud de cambio de píxeles: {total_change}")
        return total_change > movement_threshold

    return False

def frame_change_ratio(
    image_path_a: str,
    image_path_b: str,
    roi_ratio: tuple = (0.0, 0.86, 0.0, 1.0),
    pixel_threshold: int = 30
) -> float:
    """
    Proporción (0..1) de píxeles que cambian de forma apreciable entre dos fotogramas,
    restringida a una región relativa (y_start, y_end, x_start, x_end). Por defecto excluye
    el HUD inferior para medir solo la zona de rodillos.

    A diferencia de verify_spin_movement (suma absoluta), esta métrica no depende de la
    resolución y permite distinguir animaciones ambientales leves de un giro real.
    """
    img_a = cv2.imread(image_path_a, cv2.IMREAD_GRAYSCALE) if os.path.exists(image_path_a) else None
    img_b = cv2.imread(image_path_b, cv2.IMREAD_GRAYSCALE) if os.path.exists(image_path_b) else None
    if img_a is None or img_b is None:
        print("[VISION ERROR] Faltan capturas para comparar fotogramas.")
        return 0.0

    h, w = img_a.shape[:2]
    if img_b.shape[:2] != (h, w):
        img_b = cv2.resize(img_b, (w, h), interpolation=cv2.INTER_AREA)

    y1, y2 = int(h * roi_ratio[0]), int(h * roi_ratio[1])
    x1, x2 = int(w * roi_ratio[2]), int(w * roi_ratio[3])
    diff = cv2.absdiff(img_a[y1:y2, x1:x2], img_b[y1:y2, x1:x2])
    if diff.size == 0:
        return 0.0
    return float(np.count_nonzero(diff > pixel_threshold)) / diff.size
