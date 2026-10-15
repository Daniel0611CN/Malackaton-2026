import sys
from pathlib import Path

# Configuración dinámica de rutas
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
sys.path.append(str(PROJECT_ROOT))

from src.utils.ocr_helper import read_financial_zone
from src.utils.vision_helper import (
    get_dynamic_crop_roi, 
    verify_spin_movement, 
    generate_debug_image
)
from src.utils.math_checker import validate_spin_scenario

# Definición de rutas a plantillas y capturas
TEMPLATES_DIR = PROJECT_ROOT / "templates"
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"

TPL_BALANCE = str(TEMPLATES_DIR / "label_balance.png")
TPL_WAGER   = str(TEMPLATES_DIR / "label_wager.png")
TPL_WIN     = str(TEMPLATES_DIR / "label_win.png")

# Fallbacks: coordenadas manuales por si OpenCV no encuentra la plantilla
FB_BALANCE = (870, 915, 160, 350)
FB_WAGER   = (915, 955, 160, 350)
FB_WIN     = (915, 955, 400, 600)

def execute_spin_validation(image_before_path: str, image_after_path: str, debug_mode: bool = True) -> bool:
    is_test_successful = False
    
    # 1. ESCANEO DINÁMICO: Buscar las zonas a leer en la pantalla
    # Buscamos a 10 píxeles a la derecha (offset_x) de la etiqueta. Caja de 150x40 px.
    roi_balance = get_dynamic_crop_roi(image_before_path, TPL_BALANCE, offset_x=10, roi_w=150) or FB_BALANCE
    roi_wager   = get_dynamic_crop_roi(image_before_path, TPL_WAGER, offset_x=10, roi_w=150) or FB_WAGER
    roi_win     = get_dynamic_crop_roi(image_after_path, TPL_WIN, offset_x=10, roi_w=150) or FB_WIN

    if debug_mode:
        generate_debug_image(image_before_path, {
            "SALDO DETECTADO": roi_balance,
            "APUESTA DETECTADA": roi_wager,
            "PREMIO DETECTADO": roi_win
        })

    # 2. LECTURA FINANCIERA INICIAL (OCR)
    initial_balance = read_financial_zone(image_before_path, roi_balance)
    wager_amount = read_financial_zone(image_before_path, roi_wager)
    
    # 3. CONTROL DE NEGOCIO: Saldo insuficiente
    if initial_balance < wager_amount:
        print(f"ERROR: Saldo ({initial_balance} €) insuficiente para la apuesta ({wager_amount} €).")
        return False
        
    # 4. COMPROBACIÓN FÍSICA: ¿Giró la máquina?
    if verify_spin_movement(image_before_path, image_after_path):
        
        # 5. LECTURA FINANCIERA FINAL (OCR)
        final_balance = read_financial_zone(image_after_path, roi_balance)
        detected_payout = read_financial_zone(image_after_path, roi_win)
        
        # 6. ASERCIÓN MATEMÁTICA: ¿Nos han engañado?
        math_valid = validate_spin_scenario(
            initial_balance=initial_balance,
            wager=wager_amount,
            payout=detected_payout,
            final_balance=final_balance
        )
        is_test_successful = math_valid
    else:
        print("ERROR VISUAL: Los rodillos no giraron o el juego se quedó colgado.")
        
    return is_test_successful

if __name__ == "__main__":
    path_antes = str(SCREENSHOTS_DIR / "captura_antes.png")
    path_despues = str(SCREENSHOTS_DIR / "captura_despues.png")
    resultado = execute_spin_validation(path_antes, path_despues, debug_mode=True)
    print(f"Test superado: {resultado}")