import os
import json
from datetime import datetime
from typing import Dict, Any

# Carpeta estándar de capturas en la raíz del proyecto[cite: 20, 25]
SCREENSHOTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "screenshots")
)

def save_evidence_screenshot(page_or_image_path, screenshot_name: str) -> str:
    """
    Guarda o copia una captura de pantalla en la carpeta screenshots/
    para que GitHub Actions la archive como evidencia del test[cite: 4, 25].
    
    Acepta tanto el objeto 'page' de Playwright como una ruta de archivo local.
    """
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    destination_path = os.path.join(SCREENSHOTS_DIR, f"{screenshot_name}.png")

    # Si es el objeto page de Playwright
    if hasattr(page_or_image_path, "screenshot"):
        page_or_image_path.screenshot(path=destination_path)
    # Si es una ruta de imagen local que queremos archivar como evidencia
    elif isinstance(page_or_image_path, str) and os.path.exists(page_or_image_path):
        import shutil
        shutil.copy(page_or_image_path, destination_path)
    else:
        print(f"[REPORT ERROR] No se pudo guardar la evidencia para '{screenshot_name}'.")
        return ""

    print(f"[EVIDENCIA GUARDADA]: {destination_path}")
    return destination_path


def log_test_verdict(
    market: str, 
    scenario: str, 
    passed: bool, 
    details: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Registra el veredicto estructurado para el reporte del entregable[cite: 4].
    
    Args:
        market: 'betsson.com' o 'betsson.pe'[cite: 4]
        scenario: 'Scenario 1 (Real Play)' o 'Scenario 2 (Insufficient balance)'[cite: 3, 4]
        passed: True si todas las verificaciones cumplieron, False si hubo fallo[cite: 4]
        details: Diccionario con saldos leídos, wager, payout y evidencia asociada[cite: 3, 4]
    """
    verdict_entry = {
        "timestamp": datetime.now().isoformat(),
        "market": market,
        "scenario": scenario,
        "status": "PASS" if passed else "FAIL",
        "checks": details
    }

    # Guarda / anexa un resumen JSON de la ejecución
    summary_file = os.path.join(SCREENSHOTS_DIR, "validation_summary.json")
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    history = []
    if os.path.exists(summary_file):
        try:
            with open(summary_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    history.append(verdict_entry)
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

    print(f"\n[VEREDICTO REGISTRADO] {scenario} en {market}: {verdict_entry['status']}")
    return verdict_entry