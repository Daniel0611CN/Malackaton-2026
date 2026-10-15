import cv2
import numpy as np

def find_template_bounds(image_path: str, template_path: str, threshold: float = 0.7) -> tuple[int, int, int, int] | None:
    """
    Escanea la captura de pantalla buscando la plantilla pequeña.
    Devuelve (x, y, ancho, alto) de donde la ha encontrado.
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

    if img is None or template is None:
        return None

    h, w = template.shape[:2]
    # matchTemplate escanea toda la imagen buscando la máxima coincidencia
    res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    if max_val >= threshold:
        # max_loc es la coordenada (x, y) de la esquina superior izquierda donde encajó
        return (max_loc[0], max_loc[1], w, h)
    
    return None


def get_spin_coordinates_dynamic(image_path: str, template_path: str) -> tuple[int, int] | None:
    """
    Busca el botón de spin y devuelve su punto central exacto para que Playwright haga clic.
    """
    bounds = find_template_bounds(image_path, template_path)
    if bounds:
        x, y, w, h = bounds
        return (x + w // 2, y + h // 2) # Calcula el centro del botón
    return None


def get_dynamic_crop_roi(image_path: str, template_path: str, offset_x: int = 10, offset_y: int = -5, roi_w: int = 150, roi_h: int = 40) -> tuple[int, int, int, int] | None:
    """
    Busca una etiqueta (ej. "SALDO") y crea una caja de recorte (ROI) a su derecha
    para que el OCR lea solo los números.
    Devuelve el formato (y1, y2, x1, x2).
    """
    bounds = find_template_bounds(image_path, template_path)
    if bounds:
        x, y, w, h = bounds
        
        # x1, y1 es donde empieza el número (justo a la derecha de la etiqueta + un margen)
        x1 = x + w + offset_x
        y1 = y + offset_y
        
        # x2, y2 es donde termina la caja para englobar el número
        x2 = x1 + roi_w
        y2 = y1 + roi_h
        
        return (y1, y2, x1, x2)
    return None


def verify_spin_movement(image_before_path: str, image_after_path: str, threshold: float = 1000.0) -> bool:
    """
    Compara dos capturas para verificar matemáticamente si los rodillos se han movido.
    """
    img_before = cv2.imread(image_before_path, cv2.IMREAD_GRAYSCALE)
    img_after = cv2.imread(image_after_path, cv2.IMREAD_GRAYSCALE)

    if img_before is None or img_after is None:
        return False

    diff = cv2.absdiff(img_before, img_after)
    score = np.sum(diff)
    return bool(score > threshold)


def generate_debug_image(image_path: str, regions: dict, output_path: str = "screenshots/debug_detection.png") -> None:
    """
    Dibuja los recuadros calculados sobre la imagen original para que el humano compruebe si están bien.
    """
    img = cv2.imread(image_path)
    if img is None: return

    for label, roi in regions.items():
        if roi:
            y1, y2, x1, x2 = roi
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.imwrite(output_path, img)