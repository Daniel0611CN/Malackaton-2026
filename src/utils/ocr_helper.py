import os
import re
import cv2
import easyocr
from typing import Dict, Any, Tuple, Optional

# Inicialización del lector en memoria con soporte inglés y español[cite: 4, 24]
ocr_reader = easyocr.Reader(['en', 'es'], gpu=False)


def parse_numeric_and_currency(text: str) -> Tuple[float, Optional[str]]:
    """
    Parsea una cadena de texto para extraer el valor numérico (manejando formatos
    con comas y puntos de miles) y la divisa esperada (EUR o PEN)[cite: 4, 17].
    """
    cleaned = text.strip().upper()

    # 1. Identificar divisa del mercado[cite: 4]
    currency = None
    if "€" in cleaned or "EUR" in cleaned:
        currency = "EUR"
    elif "S/" in cleaned or "PEN" in cleaned or "SOLES" in cleaned or "SOL" in cleaned:
        currency = "PEN"

    # 2. Normalización de separadores de miles y decimales
    # Caso 100.000,00 -> quitar punto de miles y cambiar coma a punto
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")

    # 3. Extraer el primer valor numérico válido
    match = re.search(r'\d+(?:\.\d+)?', cleaned)
    value = float(match.group(0)) if match else 0.0

    return value, currency


def read_financial_zone(screenshot_path: str, crop_zone: Tuple[int, int, int, int]) -> Dict[str, Any]:
    """
    Recorta una zona de la pantalla, aplica OCR y extrae número, divisa y texto crudo[cite: 4, 24].

    Args:
        screenshot_path (str): Ruta de la captura completa[cite: 24].
        crop_zone (tuple): (y_start, y_end, x_start, x_end)[cite: 24].

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

    ocr_results = ocr_reader.readtext(binary, detail=0)

    if ocr_results:
        full_text = " ".join(ocr_results)
        val, curr = parse_numeric_and_currency(full_text)
        result["value"] = val
        result["currency"] = curr
        result["raw_text"] = full_text

    return result


def check_insufficient_balance_message(
    screenshot_path: str, 
    crop_zone: Optional[Tuple[int, int, int, int]] = None
) -> bool:
    """
    Valida el Escenario 2: busca en pantalla si apareció el mensaje visible
    de saldo insuficiente en español o inglés[cite: 4].

    Args:
        screenshot_path (str): Ruta de la captura completa.
        crop_zone (tuple, optional): Región a recortar. Si es None, analiza la pantalla completa.

    Returns:
        bool: True si detecta el mensaje de error de saldo insuficiente, False en caso contrario[cite: 4].
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
    texts = ocr_reader.readtext(gray, detail=0)
    full_text = " ".join(texts).lower()

    # Palabras clave del Escenario 2 en inglés y español[cite: 4]
    error_keywords = [
        "saldo insuficiente",
        "insufficient balance",
        "sin saldo",
        "no funds",
        "fondos insuficientes",
        "not enough balance"
    ]

    return any(keyword in full_text for keyword in error_keywords)