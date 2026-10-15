import os
import pytest
from src.pages.lobby_page import LobbyPage

def test_verify_game_screenshot_generated(page):
    """
    Test de CI/CD: Verifica que lobby_page.py navega hasta el juego de Pragmatic Play
    y genera la captura de pantalla inicial en /screenshots para el modulo de IA/OCR.
    """
    market = os.getenv("TARGET_MARKET", "betsson_com")
    user = os.getenv("BETSSON_USER", "")
    password = os.getenv("BETSSON_PASS", "")

    print(f"\n=== Testing screenshot generation for market: {market} ===")

    # 1. Instanciar y ejecutar el flujo de navegación de lobby_page
    lobby = LobbyPage(page, target_market=market)
    
    # Navegación y login
    lobby.navigate()
    if user and password:
        lobby.login(user, password)
    
    # Abrir el juego de Pragmatic Play
    game_loaded = lobby.open_pragmatic_game_by_provider()
    assert game_loaded is True, "Error: No se logro cargar el canvas/iframe del juego de Pragmatic Play"

    # 2. Asegurar la creación del directorio screenshots y tomar la captura del juego
    os.makedirs("screenshots", exist_ok=True)
    screenshot_path = "screenshots/game_initial_state.png"
    
    page.screenshot(path=screenshot_path)
    print(f"[CHECKPOINT IA]: Captura del juego guardada con éxito en -> {screenshot_path}")

    # 3. VERIFICACIÓN DEL TEST: Confirmar que el archivo existe y no está vacío
    assert os.path.exists(screenshot_path), "FAIL: No se creo la captura de pantalla en /screenshots"
    assert os.path.getsize(screenshot_path) > 0, "FAIL: La captura de pantalla generada esta vacia (0 bytes)"