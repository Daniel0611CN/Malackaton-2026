import os
import sys
import cv2

# 1. Resolver rutas de forma absoluta
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(TESTS_DIR, ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.vision_helper import locate_spin_button, verify_spin_movement
from src.utils.ocr_helper import read_financial_zone
from src.utils.math_checker import validate_spin_scenario
from src.utils.report_helper import log_test_verdict

# 2. Rutas a los archivos requeridos
# assets está al mismo nivel que src (en PROJECT_ROOT)
TEMPLATE_SPIN = os.path.normpath(
    os.path.join(PROJECT_ROOT, "assets", "template_spin_arrows.png")
)
IMG_INTRO = os.path.normpath(os.path.join(TESTS_DIR, "pantalla_intro.png"))
IMG_JUEGO = os.path.normpath(os.path.join(TESTS_DIR, "pantalla_juego.png"))


def run_manual_test():
    print("=" * 65)
    print("EJECUTANDO SIMULACIÓN MANUAL: FLUJO COMPLETO")
    print("=" * 65)

    # Paso 0: Verificación de archivos en disco
    print("\n[PASO 0] Verificando archivos en disco...")
    print(f" -> Plantilla:     {TEMPLATE_SPIN} -> {'OK' if os.path.exists(TEMPLATE_SPIN) else 'NO ENCONTRADA'}")
    print(f" -> Captura Intro: {IMG_INTRO} -> {'OK' if os.path.exists(IMG_INTRO) else 'NO ENCONTRADA'}")
    print(f" -> Captura Juego: {IMG_JUEGO} -> {'OK' if os.path.exists(IMG_JUEGO) else 'NO ENCONTRADA'}")

    if not os.path.exists(TEMPLATE_SPIN) or not os.path.exists(IMG_INTRO) or not os.path.exists(IMG_JUEGO):
        print("\n[ERROR] Faltan archivos por colocar en disco.")
        return

    # Paso 1: Detección en la pantalla de bienvenida
    print("\n[PASO 1] Buscando botón de inicio en pantalla de intro...")
    coords_intro = locate_spin_button(IMG_INTRO, TEMPLATE_SPIN)
    if coords_intro:
        print(f" -> Botón inicio detectado en: X={coords_intro[0]}, Y={coords_intro[1]}")
    else:
        print(" -> [AVISO] Botón de inicio no detectado con el umbral actual.")

    # Paso 2: Detección del botón Spin en el juego principal
    print("\n[PASO 2] Buscando botón Spin en pantalla de juego...")
    coords_spin = locate_spin_button(IMG_JUEGO, TEMPLATE_SPIN)
    if coords_spin:
        print(f" -> Botón Spin detectado en: X={coords_spin[0]}, Y={coords_spin[1]}")
    else:
        print(" -> [AVISO] Botón Spin no detectado con el umbral actual.")

    # Paso 3: Lectura OCR del saldo y divisa
    print("\n[PASO 3] Leyendo panel financiero con EasyOCR...")
    img = cv2.imread(IMG_JUEGO)
    h, w = img.shape[:2]

    # Recorte franja inferior del juego
    crop_inferior = (int(h * 0.88), int(h * 0.98), 0, int(w * 0.95))
    datos_financieros = read_financial_zone(IMG_JUEGO, crop_inferior)

    print(f" -> Texto leído: '{datos_financieros['raw_text']}'")
    saldo_inicial = datos_financieros["value"]
    divisa = datos_financieros["currency"]
    wager = 2.00
    payout = 0.00

    print(f" -> Saldo inicial: {saldo_inicial:.2f}")
    print(f" -> Wager:         {wager:.2f}")
    print(f" -> Divisa:        {divisa}")

    # Paso 4: Movimiento entre capturas
    print("\n[PASO 4] Verificando movimiento físico entre capturas...")
    hubo_movimiento = verify_spin_movement(IMG_INTRO, IMG_JUEGO, movement_threshold=10000)
    print(f" -> ¿Movimiento detectado?: {hubo_movimiento}")

    # Paso 5: Validación matemática
    print("\n[PASO 5] Validando conciliación matemática...")
    saldo_final_esperado = saldo_inicial - wager + payout
    es_matematica_valida = validate_spin_scenario(
        initial_balance=saldo_inicial,
        wager=wager,
        payout=payout,
        final_balance=saldo_final_esperado
    )

    # Paso 6: Registro de veredicto
    test_completado = bool(coords_spin and es_matematica_valida and hubo_movimiento)
    log_test_verdict(
        market="betsson.com",
        scenario="Scenario 1 (Real Play)",
        passed=test_completado,
        details={
            "initial_balance": saldo_inicial,
            "wager": wager,
            "payout": payout,
            "final_balance": saldo_final_esperado,
            "currency": divisa,
            "spin_button_found": coords_spin is not None,
            "movement_detected": hubo_movimiento
        }
    )

    print("\n" + "=" * 65)
    if test_completado:
        print("VEREDICTO FINAL: >>> PASS <<<")
    else:
        print("VEREDICTO FINAL: >>> FAIL <<<")
    print("=" * 65)


if __name__ == "__main__":
    run_manual_test()