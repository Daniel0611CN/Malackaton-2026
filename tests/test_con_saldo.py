import os
# from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from src.pages.lobby_page import LobbyPage
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

    # 1. Lobby: navegar y login con cuenta con saldo
    lobby = LobbyPage(page)
    lobby.navigate()
    lobby.login(
        username=os.getenv("BETSSON_COM_USER"),
        password=os.getenv("BETSSON_COM_PASS")
    )
    
    print("Balance Betsson:", lobby.get_betsson_balance_element())

    # 2. Abrir juego
    lobby.open_pragmatic_game("Gates of Olympus")

    # 3. Game: resolver DGOJ, esperar canvas y girar
    game = GamePage(page)
    game.wait_for_game_ready()
    screenshot_path = game.take_game_screenshot("evidence/test_con_saldo_ready.png")
    print(f"Captura del juego lista en: {screenshot_path}")

    game.click_spin()
    print("✅ Test con saldo finalizado con éxito.")

    page.wait_for_timeout(2000)
    browser.close()