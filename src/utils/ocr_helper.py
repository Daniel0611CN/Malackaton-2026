import os
import re
import cv2
from typing import Dict, Any, List, Tuple, Optional

# El lector de EasyOCR se carga bajo demanda (cargar el modelo de PyTorch tarda varios
# segundos y no queremos pagarlo al importar el módulo).
_ocr_reader = None


def get_ocr_reader():
    global _ocr_reader
    if _ocr_reader is None:
        import easyocr
        _ocr_reader = easyocr.Reader(['en', 'es'], gpu=False, verbose=False)
    return _ocr_reader


# Etiquetas por defecto del HUD de Pragmatic Play (inglés y español)
DEFAULT_HUD_LABELS = {
    "credit": ["CREDIT", "CRÉDITO", "CREDITO", "SALDO", "BALANCE"],
    "bet": ["BET", "APUESTA"],
    "win": ["WIN", "GANANCIA", "PREMIO", "GANADO"],
}

AMOUNT_REGEX = re.compile(r'\d[\d.,]*')


def parse_numeric_and_currency(text: str) -> Tuple[float, Optional[str]]:
    """
    Parsea una cadena de texto para extraer el valor numérico (manejando formatos
    con comas y puntos de miles) y la divisa (EUR).
    """
    cleaned = text.strip().upper()

    # 1. Identificar divisa del mercado
    currency = None
    if "€" in cleaned or "EUR" in cleaned:
        currency = "EUR"

    match = AMOUNT_REGEX.search(cleaned)
    if not match:
        return 0.0, currency
    number = match.group(0).rstrip(".,")

    # 2. Normalización de separadores de miles y decimales
    if "," in number and "." in number:
        # 100.000,00 -> el último separador es el decimal
        if number.rfind(",") > number.rfind("."):
            number = number.replace(".", "").replace(",", ".")
        else:
            number = number.replace(",", "")
    elif "," in number:
        # 2,00 -> decimal ; 1,000 -> miles
        parts = number.split(",")
        if len(parts) == 2 and len(parts[1]) != 3:
            number = number.replace(",", ".")
        else:
            number = number.replace(",", "")
    elif number.count(".") > 1 or (number.count(".") == 1 and len(number.split(".")[1]) == 3):
        # 100.000 -> miles
        number = number.replace(".", "")

    try:
        value = float(number)
    except ValueError:
        value = 0.0

    return value, currency


def read_financial_zone(screenshot_path: str, crop_zone: Tuple[int, int, int, int]) -> Dict[str, Any]:
    """
    Recorta una zona de la pantalla, aplica OCR y extrae número, divisa y texto crudo.

    Args:
        screenshot_path (str): Ruta de la captura completa.
        crop_zone (tuple): (y_start, y_end, x_start, x_end).

    Returns:
        dict: {"value": float, "currency": str | None, "raw_text": str}
    """
    result = {
        "value": 0.0,
        "currency": None,
        "raw_text": ""
    }

    if not os.path.exists(screenshot_path):
        print(f"[OCR ERROR] Screenshot no encontrado en '{screenshot_path}'.")
        return result

    image = cv2.imread(screenshot_path)
    if image is None:
        print(f"[OCR ERROR] No se pudo leer la imagen en '{screenshot_path}'.")
        return result

    y1, y2, x1, x2 = crop_zone
    cropped = image[y1:y2, x1:x2]

    if cropped.size == 0:
        print("[OCR ERROR] La zona de recorte está vacía.")
        return result

    # Preprocesamiento para mejorar contraste de caracteres
    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    ocr_results = get_ocr_reader().readtext(binary, detail=0)

    if ocr_results:
        full_text = " ".join(ocr_results)
        val, curr = parse_numeric_and_currency(full_text)
        result["value"] = val
        result["currency"] = curr
        result["raw_text"] = full_text

    return result


def read_text_tokens(
    image_path: str,
    crop_ratio: Optional[Tuple[float, float, float, float]] = None,
    upscale: float = 1.0
) -> List[Dict[str, Any]]:
    """
    Ejecuta OCR sobre una imagen (o una región relativa de ella) y devuelve los tokens
    con su caja en coordenadas de la imagen original.

    Args:
        crop_ratio: (y_start, y_end, x_start, x_end) en proporciones 0..1, o None para toda la imagen.
        upscale: factor de ampliación previo al OCR (el texto pequeño del HUD lo necesita).
    """
    image = cv2.imread(image_path) if os.path.exists(image_path) else None
    if image is None:
        print(f"[OCR ERROR] No se pudo leer la imagen en '{image_path}'.")
        return []

    h, w = image.shape[:2]
    y1, y2, x1, x2 = (0, h, 0, w)
    if crop_ratio is not None:
        y1, y2 = int(h * crop_ratio[0]), int(h * crop_ratio[1])
        x1, x2 = int(w * crop_ratio[2]), int(w * crop_ratio[3])
    region = image[y1:y2, x1:x2]
    if region.size == 0:
        return []

    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    if upscale != 1.0:
        gray = cv2.resize(gray, None, fx=upscale, fy=upscale, interpolation=cv2.INTER_CUBIC)

    tokens = []
    for bbox, text, conf in get_ocr_reader().readtext(gray):
        xs = [p[0] / upscale + x1 for p in bbox]
        ys = [p[1] / upscale + y1 for p in bbox]
        tokens.append({
            "text": text,
            "conf": float(conf),
            "x1": min(xs), "x2": max(xs),
            "y1": min(ys), "y2": max(ys),
        })
    return tokens


def _matches_label(text: str, labels: List[str]) -> Optional[str]:
    upper = text.upper()
    for label in labels:
        if label.upper() in upper:
            return label
    return None


def _amount_after_label(text: str, label: str, all_labels: List[str]) -> Optional[str]:
    rest = text.upper().split(label.upper(), 1)[1]
    # Cortar en la siguiente etiqueta: "CRÉDITO 100,00 € APUESTA 2,00 €" -> "100,00 €"
    cut = min([rest.find(other.upper()) for other in all_labels if other.upper() in rest] or [len(rest)])
    rest = rest[:cut]
    return rest if AMOUNT_REGEX.search(rest) else None


def read_game_hud(
    image_path: str,
    labels: Optional[Dict[str, List[str]]] = None,
    crop_ratio: Tuple[float, float, float, float] = (0.86, 1.0, 0.0, 1.0)
) -> Dict[str, Any]:
    """
    Lee el HUD inferior del juego (p. ej. "CRÉDITO 100.000,00 €  APUESTA 2,00 €").

    Localiza cada etiqueta (CREDIT/CRÉDITO, BET/APUESTA, WIN/GANANCIA) por OCR y toma como
    valor el token numérico más cercano a su derecha (o debajo), sin coordenadas fijas.

    Returns:
        dict: {"credit": float|None, "bet": float|None, "win": float|None,
               "currency": str|None, "raw_text": str}
    """
    labels = labels or DEFAULT_HUD_LABELS
    all_labels = sum(labels.values(), [])
    tokens = read_text_tokens(image_path, crop_ratio=crop_ratio, upscale=3.0)
    result: Dict[str, Any] = {"credit": None, "bet": None, "win": None, "currency": None,
                              "raw_text": " | ".join(t["text"] for t in tokens)}
    currencies = []

    for field, field_labels in labels.items():
        for tok in tokens:
            label = _matches_label(tok["text"], field_labels)
            if not label:
                continue

            # Caso 1: etiqueta y cantidad en el mismo token ("CRÉDITO 100.000,00 €")
            amount_text = _amount_after_label(tok["text"], label, all_labels)

            # Caso 2: la cantidad es el token numérico más cercano a la derecha o debajo
            if amount_text is None:
                height = max(tok["y2"] - tok["y1"], 1)
                best, best_dist = None, None
                for other in tokens:
                    if other is tok or not AMOUNT_REGEX.search(other["text"]):
                        continue
                    if _matches_label(other["text"], all_labels):
                        continue
                    same_line = abs((other["y1"] + other["y2"]) / 2 - (tok["y1"] + tok["y2"]) / 2) < height * 1.2
                    right = other["x1"] >= tok["x2"] - height
                    below = other["y1"] >= tok["y1"] and other["y1"] - tok["y2"] < height * 2
                    if same_line and right:
                        dist = other["x1"] - tok["x2"]
                    elif below and abs(other["x1"] - tok["x1"]) < height * 6:
                        dist = 1000 + other["y1"] - tok["y2"]
                    else:
                        continue
                    if best_dist is None or dist < best_dist:
                        best, best_dist = other, dist
                if best is None:
                    continue
                amount_text = best["text"]
                # El símbolo de divisa puede estar en un token aparte, justo después ("2,00" "€")
                for other in tokens:
                    if other is not best and abs(other["x1"] - best["x2"]) < height * 1.5 \
                            and abs(other["y1"] - best["y1"]) < height:
                        amount_text += " " + other["text"]

            value, currency = parse_numeric_and_currency(amount_text)
            result[field] = value
            if currency:
                currencies.append(currency)
            break

    if currencies:
        result["currency"] = max(set(currencies), key=currencies.count)
    else:
        _, result["currency"] = parse_numeric_and_currency(result["raw_text"])
    return result


def find_amounts_on_screen(image_path: str) -> List[float]:
    """Devuelve todas las cantidades numéricas visibles en la imagen (para localizar el premio)."""
    values = []
    for tok in read_text_tokens(image_path, upscale=1.5):
        if AMOUNT_REGEX.search(tok["text"]):
            value, _ = parse_numeric_and_currency(tok["text"])
            values.append(value)
    return values


def read_screen_text(image_path: str) -> str:
    """Texto completo visible en una captura (en minúsculas)."""
    return " ".join(t["text"] for t in read_text_tokens(image_path, upscale=1.0)).lower()


def find_keywords(text: str, keywords: List[str]) -> List[str]:
    lowered = text.lower()
    return [kw for kw in keywords if kw.lower() in lowered]


def check_insufficient_balance_message(
    screenshot_path: str,
    crop_zone: Optional[Tuple[int, int, int, int]] = None,
    keywords: Optional[List[str]] = None
) -> bool:
    """
    Valida el Escenario 2: busca en pantalla si apareció el mensaje visible
    de saldo insuficiente en español o inglés.

    Args:
        screenshot_path (str): Ruta de la captura completa.
        crop_zone (tuple, optional): Región a recortar. Si es None, analiza la pantalla completa.
        keywords (list, optional): Palabras clave a buscar (por defecto, inglés y español).

    Returns:
        bool: True si detecta el mensaje de error de saldo insuficiente, False en caso contrario.
    """
    if not os.path.exists(screenshot_path):
        return False

    image = cv2.imread(screenshot_path)
    if image is None:
        return False

    if crop_zone is not None:
        y1, y2, x1, x2 = crop_zone
        image = image[y1:y2, x1:x2]

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    texts = get_ocr_reader().readtext(gray, detail=0)
    full_text = " ".join(texts).lower()

    # Palabras clave del Escenario 2 en inglés y español
    error_keywords = keywords or [
        "saldo insuficiente",
        "insufficient balance",
        "sin saldo",
        "no funds",
        "fondos insuficientes",
        "not enough balance"
    ]

    return bool(find_keywords(full_text, error_keywords))
