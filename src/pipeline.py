import sys
from pathlib import Path

# Añade la raíz del repositorio al path de Python dinámicamente
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.utils.ocr_helper import read_financial_zone
from src.utils.vision_helper import verify_spin_movement
from src.utils.math_checker import validate_spin_scenario

# Constantes de recorte para 1920x1080 (provisionales hasta recibir la captura final de Playwright)
CROP_BETSSON_BALANCE = (15, 55, 1120, 1300)
CROP_GAME_CREDIT     = (870, 915, 160, 350)
CROP_GAME_WAGER      = (915, 955, 160, 350)

def execute_spin_validation(image_before_path: str, image_after_path: str, expected_payout: float = 0.0) -> bool:
    """
    Orchestrates the entire end-to-end verification process for a single spin cycle.
    
    Args:
        image_before_path (str): File path to the screenshot taken before initiating the spin.
        image_after_path (str): File path to the screenshot taken after the spin cycle finishes.
        expected_payout (float): The winning payout amount expected for the spin (defaults to 0.0).
        
    Returns:
        bool: True if movement is confirmed and financial balance reconciles, False otherwise.
    """
    is_test_successful = False
    
    # 1. Lectura del estado financiero inicial
    initial_balance = read_financial_zone(image_before_path, CROP_GAME_CREDIT)
    wager_amount = read_financial_zone(image_before_path, CROP_GAME_WAGER)
    
    # 2. Verificación de movimiento de rodillos por matriz
    has_reels_moved = verify_spin_movement(image_before_path, image_after_path)
    
    if has_reels_moved:
        # 3. Lectura del estado financiero final
        final_balance = read_financial_zone(image_after_path, CROP_GAME_CREDIT)
        
        # 4. Aserción matemática de la regla de casino
        math_valid = validate_spin_scenario(
            initial_balance=initial_balance,
            wager=wager_amount,
            payout=expected_payout,
            final_balance=final_balance
        )
        
        is_test_successful = math_valid
    else:
        print("Error: Visual verification failed. The game reels did not rotate.")
        
    return is_test_successful


if __name__ == "__main__":
    # Test rápido de ejecución local
    path_before = "captura_antes.png"
    path_after = "captura_despues.png"
    
    result = execute_spin_validation(path_before, path_after)
    print(f"Pipeline Test Execution Result: {result}")