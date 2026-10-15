import sys
from pathlib import Path

# 1. Definición de rutas del proyecto
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"

# Añade la raíz del repositorio al path de Python dinámicamente
sys.path.append(str(PROJECT_ROOT))

from src.utils.ocr_helper import read_financial_zone
from src.utils.vision_helper import verify_spin_movement
from src.utils.math_checker import validate_spin_scenario

# Constantes de recorte para 1920x1080 (provisionales hasta calibrar con la foto real)
CROP_BETSSON_BALANCE = (15, 55, 1120, 1300)
CROP_GAME_CREDIT     = (870, 915, 160, 350)
CROP_GAME_WAGER      = (915, 955, 160, 350)
CROP_GAME_WIN        = (915, 955, 400, 600)


def execute_spin_validation(image_before_path: str, image_after_path: str) -> bool:
    """
    Orchestrates the entire end-to-end verification process for a single spin cycle.
    
    Args:
        image_before_path (str): Path to the screenshot taken before initiating the spin.
        image_after_path (str): Path to the screenshot taken after the spin finishes.
        
    Returns:
        bool: True if movement is confirmed and financial balance reconciles, False otherwise.
    """
    is_test_successful = False
    
    # 1. Lectura del estado financiero inicial mediante OCR
    initial_balance = read_financial_zone(image_before_path, CROP_GAME_CREDIT)
    wager_amount = read_financial_zone(image_before_path, CROP_GAME_WAGER)
    
    # Guardia de negocio: Verificar saldo suficiente antes de girar
    if initial_balance < wager_amount:
        print(f"ERROR: Saldo insuficiente ({initial_balance} €) para la apuesta ({wager_amount} €).")
        return is_test_successful
    
    # 2. Verificación de movimiento de rodillos por matriz de diferencia
    has_reels_moved = verify_spin_movement(image_before_path, image_after_path)
    
    if has_reels_moved:
        # 3. Lectura del estado financiero final y del premio mediante OCR
        final_balance = read_financial_zone(image_after_path, CROP_GAME_CREDIT)
        detected_payout = read_financial_zone(image_after_path, CROP_GAME_WIN)
        
        # 4. Aserción matemática de la regla de casino
        math_valid = validate_spin_scenario(
            initial_balance=initial_balance,
            wager=wager_amount,
            payout=detected_payout,
            final_balance=final_balance
        )
        
        is_test_successful = math_valid
    else:
        print("Error: Visual verification failed. The game reels did not rotate.")
        
    return is_test_successful


if __name__ == "__main__":
    # Prueba rápida buscando las imágenes en la carpeta screenshots/ de la raíz
    path_before = str(SCREENSHOTS_DIR / "captura_antes.png")
    path_after = str(SCREENSHOTS_DIR / "captura_despues.png")
    
    result = execute_spin_validation(path_before, path_after)
    print(f"Pipeline Test Execution Result: {result}")