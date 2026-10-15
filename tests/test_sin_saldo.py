import os
# from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from src.pages.lobby_page import LobbyPage, InsufficientFundsError
from src.pages.game_page import GamePage

# load_dotenv()

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
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
    page.add_init_script("delete Object.getPrototypeOf(navigator).webdriver")

    # 1. Lobby: navegar y login con cuenta de saldo 0
    lobby = LobbyPage(page)
    lobby.navigate()
    lobby.login(
        username=os.getenv("BETSSON_NOFUND_USER"),
        password=os.getenv("BETSSON_NOFUND_PASS")
    )

    try:
        balance = lobby.get_betsson_balance_element()
        print(f"Balance detectado en lobby: {balance}")
    except Exception as e:
        print(f"Aviso leyendo balance: {e}")

    # 2. Intentar flujo de juego controlando la excepción esperada
    game = GamePage(page)
    banner_detectado = False

    try:
        print("Lanzando juego para verificar detección de saldo insuficiente...")
        lobby.open_pragmatic_game("Gates of Olympus")
        game.wait_for_game_ready()
        game.click_spin()

    except InsufficientFundsError as e:
        banner_detectado = True
        print("\n" + "=" * 55)
        print("✅ TEST SIN SALDO PASADO: Banner detectado correctamente")
        print(f"Detalle: {e}")
        print("=" * 55 + "\n")

    except Exception as e:
        print(f"❌ Falló por un error imprevisto: {e}")

    if not banner_detectado:
        print("⚠️ ALERTA: No se detectó ningún banner de saldo insuficiente.")

    page.wait_for_timeout(2000)
    browser.close()