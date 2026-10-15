import os

def save_evidence_screenshot(page, screenshot_name):
    """
    Guarda una captura de pantalla en la carpeta /screenshots
    para que GitHub Actions la suba como evidencia
    """
    os.makedirs("screenshots", exist_ok=True)
    path = f"screenshots/{screenshot_name}.png"
    page.screenshot(path=path)
    print(f"[EVIDENCIA GUARDADA]: {path}")
    return path