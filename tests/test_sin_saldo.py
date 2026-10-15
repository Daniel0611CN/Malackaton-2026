import os
from playwright.sync_api import sync_playwright
from src.pages.lobby_page import LobbyPage
from src.pages.game_page import GamePage

with sync_playwright() as p:
    # Flags para evitar detección de bots y bloqueos WAF
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--start-maximized",
            "--no-sandbox"
        ]
    )
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    page = context.new_page()

    # Ocultar webdriver
    page.add_init_script("delete Object.getPrototypeOf(navigator).webdriver")

    # Inicializar Lobby (apunta por defecto a betsson.com)
    lobby = LobbyPage(page)
    lobby.navigate()
    lobby.login2()
    
    print("Balance Betsson:", lobby.get_betsson_balance_element())

    # Abre la slot de Pragmatic Play en .com
    lobby.open_pragmatic_game("Gates of Olympus")

    # Módulo de control del canvas
    game = GamePage(page)
    game.wait_for_game_ready()
    screenshot_path = game.take_game_screenshot("evidence/test_ready.png")
    print(f"Captura del juego lista en: {screenshot_path}")

    # Simular giro
    game.click_spin()

    # Validar que salta el aviso de saldo insuficiente y guardar captura
    sin_saldo = game.verify_insufficient_funds_modal("evidence/test_sin_saldo.png")

    # Espera visual antes de desmontar sesión
    page.wait_for_timeout(20000)
    browser.close()

    # Aserción final del test
    assert sin_saldo, "Fallo: No se mostró la alerta de saldo insuficiente tras pulsar el botón de giro."
    
    # Pausa de 5 segundos para que veas el resultado antes de cerrar
    # page.wait_for_timeout(2000)
    browser.close()