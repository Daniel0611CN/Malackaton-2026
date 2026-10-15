# import os
# from dotenv import load_dotenv
# from playwright.sync_api import Page, TimeoutError

# load_dotenv()

# class LobbyPage:
#     def __init__(self, page: Page):
#         self.page = page
#         self.base_url = "https://www.betsson.com"

#     def navigate(self):
#         """Abre la página principal y descarta pop-ups."""
#         self.page.goto(self.base_url, wait_until="domcontentloaded")
#         self.handle_popups()

#     def handle_popups(self):
#         """Cierra banners de cookies, pop-ups y el modal de Passkey / Claves de acceso."""
#         dismiss_selectors = [
#             # 1. Descarte del modal de Passkey / Claves de acceso
#             "button:has-text('No ahora')",
#             "button:has-text('Not now')",
#             "button:has-text('Cancelar')",
#             "button:has-text('Cancel')",
#             "button:has-text('Saltar por ahora')",
#             "button:has-text('Skip for now')",
#             "[data-test-id*='passkey'] button:has-text('No')",
#             "[data-test-id*='passkey-cancel']",
#             "[data-test-id*='dismiss']",
#             # 2. Cookies y consentimientos estándar
#             "#onetrust-accept-btn-handler",
#             "button#accept-recommended-btn-handler",
#             "button:has-text('Accept all')",
#             "button:has-text('Accept All Cookies')",
#             "button:has-text('Aceptar todas')",
#             "button:has-text('Aceptar')",
#             "button:has-text('Continue')"
#         ]

#         for sel in dismiss_selectors:
#             try:
#                 locator = self.page.locator(sel).first
#                 if locator.is_visible(timeout=1000):
#                     locator.click()
#                     self.page.wait_for_timeout(500)
#             except Exception:
#                 pass

#     def login(self):
#         """Inicia sesión interactuando como un usuario real en betsson.com."""
#         username = os.environ.get("BETSSON_COM_USER")
#         password = os.environ.get("BETSSON_COM_PASS")

#         if not username or not password:
#             raise ValueError("Faltan credenciales: BETSSON_COM_USER o BETSSON_COM_PASS en el entorno (.env).")

#         self.handle_popups()

#         # 1. Click en el botón Iniciar sesión usando data-test-id
#         login_btn = self.page.locator("[data-test-id='login-button']").first
#         login_btn.wait_for(state="visible", timeout=10000)
#         login_btn.click()

#         # 2. Esperar a que la página cambie a la pantalla de login o abra el modal
#         self.page.wait_for_load_state("domcontentloaded")
#         self.page.wait_for_timeout(2000)

#         # 3. Localizar input de usuario / email
#         user_input = self.page.locator("input[type='email'], input[type='text'], input[name='username']").first
#         try:
#             user_input.wait_for(state="visible", timeout=15000)
#         except Exception:
#             os.makedirs("evidence", exist_ok=True)
#             self.page.screenshot(path="evidence/debug_modal.png")
#             raise RuntimeError("La pantalla sigue sin mostrar inputs. Revisa evidence/debug_modal.png")

#         user_input.click()
#         user_input.fill(username)

#         # 4. Input de password
#         pass_input = self.page.locator("input[type='password']").first
#         pass_input.wait_for(state="visible", timeout=5000)
#         pass_input.click()
#         pass_input.fill(password)

#         # 5. Enviar el formulario pulsando Enter en el campo de password
#         pass_input.press("Enter")

#         self.page.wait_for_timeout(2500)

#         # Cerrar el modal de passkey si aparece
#         self.handle_popups()

#         # Opcional: si el modal bloquea con overlay o tecla Escape
#         self.page.keyboard.press("Escape")
#         self.page.wait_for_timeout(1000)
#         self.handle_popups()

#         # Fallback por si Enter no dispara el submit:
#         try:
#             submit_btn = self.page.locator(
#                 "button[type='submit'], [data-test-id*='login-submit'], [data-test-id*='submit'], button:has-text('Log in'), button:has-text('Sign in')"
#             ).first
#             if submit_btn.is_visible(timeout=1500):
#                 submit_btn.click(timeout=1500)
#         except Exception:
#             pass

#         # 6. Esperar a que el login se procese y la página vuelva al lobby
#         self.page.wait_for_timeout(4000)
#         self.handle_popups()

#     def get_betsson_balance_element(self) -> str:
#         """
#         Lee el saldo visible en el header tras loguearse.
#         Filtra únicamente elementos que estén visibles en pantalla para evitar botones colapsados.
#         """
#         # Aseguramos que el botón de login ya no esté visible (confirmando que estamos dentro)
#         try:
#             self.page.locator("[data-test-id='login-button']").first.wait_for(state="hidden", timeout=5000)
#         except Exception:
#             pass

#         # Selectores específicos de saldo visibles en escritorio
#         balance_candidates = [
#             # Selector específico de texto monetario visible
#             "user-balance-header:visible",
#             "[data-test-id='user-balance']:visible",
#             ".amount-money:visible",
#             "[data-test-id*='balance']:not(button):visible",
#             ".balance-panel:not(.balance-panel-hide) .amount-money:visible",
#             # Fallback: cualquier contenedor en el header que muestre moneda (€ o S/)
#             "header-brand-secondary-panel span:has-text('€'):visible",
#             "header-brand-secondary-panel span:has-text('S/'):visible",
#             "header-brand-secondary-panel [class*='amount']:visible"
#         ]

#         for sel in balance_candidates:
#             loc = self.page.locator(sel).first
#             try:
#                 if loc.is_visible(timeout=1500):
#                     text = loc.inner_text().strip()
#                     if text:
#                         return text
#             except Exception:
#                 continue

#         # Si aún no lo encuentra por timing, sacamos captura para ver el header real
#         os.makedirs("evidence", exist_ok=True)
#         self.page.screenshot(path="evidence/debug_balance.png")
#         raise RuntimeError("No se encontró el saldo visible en el header. Revisa evidence/debug_balance.png")

#     def open_pragmatic_game(self, game_name: str = "Gates of Olympus"):
#         """
#         1. Entrar en la sección Casino.
#         2. Bajar hasta encontrar la sección/carrusel de 'Proveedores'.
#         3. Hacer click en 'Pragmatic Play'.
#         4. Seleccionar y lanzar el juego (ej. Gates of Olympus).
#         """
#         print("Paso 1: Entrando en Casino...")
#         self.page.keyboard.press("Escape")
#         self.handle_popups()

#         # Click en la pestaña de Casino
#         casino_tab = self.page.locator(
#             "[data-test-id='fdsp-tab-product.casino'] a, [data-test-id='fdsp-tab-product.casino'], a[href*='/casino']:visible"
#         ).first
        
#         try:
#             if casino_tab.is_visible(timeout=2000):
#                 casino_tab.click(force=True)
#             else:
#                 self.page.goto(f"{self.base_url}/casino", wait_until="domcontentloaded")
#         except Exception:
#             self.page.goto(f"{self.base_url}/casino", wait_until="domcontentloaded")

#         self.page.wait_for_timeout(2500)
#         self.handle_popups()

#         print("Paso 2: Scrolleando hasta la sección 'Proveedores'...")
#         # Localizador de la tarjeta/logo de Pragmatic Play en la cuadrícula de proveedores
#         pragmatic_card = self.page.locator(
#             "a[href*='proveedores/pragmatic'], a[href*='providers/pragmatic'], img[alt*='Pragmatic' i], [data-test-id*='pragmatic']"
#         ).first

#         # Scroll progresivo hacia abajo hasta que el lazy load renderice el bloque de proveedores
#         found_provider = False
#         for _ in range(15):
#             try:
#                 if pragmatic_card.is_visible(timeout=400):
#                     found_provider = True
#                     break
#             except Exception:
#                 pass
#             self.page.evaluate("window.scrollBy(0, 700)")
#             self.page.wait_for_timeout(400)

#         print("Paso 3: Click en 'Pragmatic Play'...")
#         if found_provider:
#             pragmatic_card.scroll_into_view_if_needed()
#             self.page.wait_for_timeout(500)
#             pragmatic_card.click(force=True)
#         else:
#             # Fallback seguro en caso de que el layout del viewport no lo muestre
#             self.page.goto(f"{self.base_url}/casino/proveedores/pragmatic-play", wait_until="domcontentloaded")

#         self.page.wait_for_timeout(3000)
#         self.handle_popups()

#         # Guardar captura que acredita la Parte 1 completada
#         os.makedirs("evidence", exist_ok=True)
#         self.page.screenshot(path="evidence/parte1_pragmatic_lobby.png")
#         print("✅ Parte 1 completada: catálogo de Pragmatic Play abierto.")

#         # Paso 4: Lanzar el juego
#         print(f"Paso 4: Buscando y abriendo '{game_name}'...")
#         game_slug = game_name.lower().replace(" ", "-")
#         game_card = self.page.locator(
#             f"a[href*='{game_slug}'], [data-test-id*='{game_slug}'], a:has-text('{game_name}')"
#         ).first

#         for _ in range(5):
#             if game_card.is_visible():
#                 break
#             self.page.evaluate("window.scrollBy(0, 500)")
#             self.page.wait_for_timeout(400)

#         game_card.scroll_into_view_if_needed()
#         game_card.click(force=True)
#         self.page.wait_for_timeout(1500)

#         # Si aparece el botón de confirmación "Jugar" / "Play"
#         play_btn = self.page.locator("button:has-text('Jugar'), button:has-text('Play'), a:has-text('Jugar'), a:has-text('Play')").first
#         try:
#             if play_btn.is_visible(timeout=3000):
#                 play_btn.click(force=True)
#         except Exception:
#             pass

#         print(f"Lanzando '{game_name}'...")

import os
from dotenv import load_dotenv
from playwright.sync_api import Page, TimeoutError

load_dotenv()


class InsufficientFundsError(Exception):
    """Excepción lanzada cuando el usuario no tiene saldo suficiente para abrir el juego."""
    pass


class LobbyPage:
    def __init__(self, page: Page):
        self.page = page
        self.base_url = "https://www.betsson.com"

    def navigate(self):
        """Abre la página principal y descarta pop-ups."""
        self.page.goto(self.base_url, wait_until="domcontentloaded")
        self.handle_popups()

    def handle_popups(self):
        """Cierra banners de cookies, pop-ups y el modal de Passkey / Claves de acceso."""
        dismiss_selectors = [
            # 1. Descarte del modal de Passkey / Claves de acceso
            "button:has-text('No ahora')",
            "button:has-text('Not now')",
            "button:has-text('Cancelar')",
            "button:has-text('Cancel')",
            "button:has-text('Saltar por ahora')",
            "button:has-text('Skip for now')",
            "[data-test-id*='passkey'] button:has-text('No')",
            "[data-test-id*='passkey-cancel']",
            "[data-test-id*='dismiss']",
            # 2. Cookies y consentimientos estándar
            "#onetrust-accept-btn-handler",
            "button#accept-recommended-btn-handler",
            "button:has-text('Accept all')",
            "button:has-text('Accept All Cookies')",
            "button:has-text('Aceptar todas')",
            "button:has-text('Aceptar')",
            "button:has-text('Continue')"
        ]

        for sel in dismiss_selectors:
            try:
                locator = self.page.locator(sel).first
                if locator.is_visible(timeout=1000):
                    locator.click()
                    self.page.wait_for_timeout(500)
            except Exception:
                pass

    def check_insufficient_credits(self, timeout_ms: int = 1500) -> bool:
        """
        Detecta si aparece el banner o modal indicando falta de saldo/créditos
        tras intentar abrir un juego o navegar.
        """
        text_patterns = [
            "saldo insuficiente",
            "sin saldo",
            "no tienes saldo",
            "fondos insuficientes",
            "no tienes créditos",
            "créditos insuficientes",
            "insufficient funds",
            "insufficient balance",
            "not enough balance",
            "ingresar saldo",
            "depositar"
        ]

        selector_query = (
            "[data-test-id*='insufficient-funds'], "
            "[data-test-id*='low-balance'], "
            "[data-test-id*='deposit-banner'], "
            "[data-test-id*='no-credit'], "
            "[role='alert'], "
            ".banner-insufficient-funds, "
            ".deposit-modal"
        )

        # Chequeo por selectores
        try:
            banner = self.page.locator(selector_query).first
            if banner.is_visible(timeout=timeout_ms):
                print("⚠️ Banner de falta de fondos detectado por selector.")
                return True
        except Exception:
            pass

        # Chequeo por texto visible
        for pattern in text_patterns:
            try:
                locator = self.page.locator(f"text=/{pattern}/i").first
                if locator.is_visible(timeout=200):
                    print(f"⚠️ Aviso de falta de saldo detectado por texto: '{pattern}'")
                    return True
            except Exception:
                pass

        # Búsqueda en Shadow DOM
        has_banner_js = self.page.evaluate("""() => {
            const keywords = [
                'saldo insuficiente', 'sin saldo', 'no tienes saldo',
                'fondos insuficientes', 'no tienes créditos', 'créditos insuficientes',
                'insufficient funds', 'insufficient balance', 'depositar'
            ];

            function searchNodes(root = document) {
                const candidates = root.querySelectorAll("[role='alert'], [data-test-id*='balance'], [data-test-id*='deposit'], [class*='banner'], [class*='modal']");
                for (const el of candidates) {
                    const text = (el.innerText || el.textContent || '').toLowerCase();
                    if (keywords.some(kw => text.includes(kw))) {
                        return true;
                    }
                }
                for (const el of root.querySelectorAll('*')) {
                    if (el.shadowRoot) {
                        if (searchNodes(el.shadowRoot)) return true;
                    }
                }
                return false;
            }

            return searchNodes(document);
        }""")

        return bool(has_banner_js)

    def login(self, username: str = None, password: str = None):
            """Inicia sesión interactuando como un usuario real en betsson.com."""
            username = (
                username
                or os.getenv("BETSSON_NOFUND_USER")
                or os.getenv("BETSSON_COM_USER")
            )
            password = (
                password
                or os.getenv("BETSSON_NOFUND_PASS")
                or os.getenv("BETSSON_COM_PASS")
            )
    
            if not username or not password:
                raise ValueError(
                    "Faltan credenciales: define BETSSON_COM_USER/PASS o BETSSON_NOFUND_USER/PASS en .env, "
                    "o pásalas como argumentos a login()."
                )
    
            # 1. Click en el botón Iniciar sesión usando data-test-id
            login_btn = self.page.locator("[data-test-id='login-button']").first
            login_btn.wait_for(state="visible", timeout=10000)
            login_btn.click()
    
            # 2. Esperar a que la página cambie a la pantalla de login o abra el modal
            self.page.wait_for_load_state("domcontentloaded")
            self.page.wait_for_timeout(2000)
    
            # 3. Localizar input de usuario / email
            user_input = self.page.locator("input[type='email'], input[type='text'], input[name='username']").first
            try:
                user_input.wait_for(state="visible", timeout=15000)
            except Exception:
                os.makedirs("evidence", exist_ok=True)
                self.page.screenshot(path="evidence/debug_modal.png")
                raise RuntimeError("La pantalla sigue sin mostrar inputs. Revisa evidence/debug_modal.png")
    
            user_input.click()
            user_input.fill(username)
    
            # 4. Input de password
            pass_input = self.page.locator("input[type='password']").first
            pass_input.wait_for(state="visible", timeout=5000)
            pass_input.click()
            pass_input.fill(password)
    
            # 5. Enviar el formulario pulsando Enter en el campo de password
            pass_input.press("Enter")
            self.page.wait_for_timeout(2500)
    
            # Cerrar posibles modales
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(1000)
    
            # Fallback por si Enter no dispara el submit
            try:
                submit_btn = self.page.locator(
                    "button[type='submit'], [data-test-id*='login-submit'], [data-test-id*='submit'], button:has-text('Log in'), button:has-text('Sign in')"
                ).first
                if submit_btn.is_visible(timeout=1500):
                    submit_btn.click(timeout=1500)
            except Exception:
                pass
    
            # 6. Esperar a que el login se procese
            self.page.wait_for_timeout(4000)

    def get_betsson_balance_element(self) -> str:
        """
        Lee el saldo visible en el header tras loguearse.
        Filtra únicamente elementos que estén visibles en pantalla para evitar botones colapsados.
        """
        try:
            self.page.locator("[data-test-id='login-button']").first.wait_for(state="hidden", timeout=5000)
        except Exception:
            pass

        balance_candidates = [
            "user-balance-header:visible",
            "[data-test-id='user-balance']:visible",
            ".amount-money:visible",
            "[data-test-id*='balance']:not(button):visible",
            ".balance-panel:not(.balance-panel-hide) .amount-money:visible",
            "header-brand-secondary-panel span:has-text('€'):visible",
            "header-brand-secondary-panel span:has-text('S/'):visible",
            "header-brand-secondary-panel [class*='amount']:visible"
        ]

        for sel in balance_candidates:
            loc = self.page.locator(sel).first
            try:
                if loc.is_visible(timeout=1500):
                    text = loc.inner_text().strip()
                    if text:
                        return text
            except Exception:
                continue

        os.makedirs("evidence", exist_ok=True)
        self.page.screenshot(path="evidence/debug_balance.png")
        raise RuntimeError("No se encontró el saldo visible en el header. Revisa evidence/debug_balance.png")

    def open_pragmatic_game(self, game_name: str = "Gates of Olympus"):
        """
        1. Entrar en la sección Casino.
        2. Bajar hasta encontrar la sección/carrusel de 'Proveedores'.
        3. Hacer click en 'Pragmatic Play'.
        4. Seleccionar y lanzar el juego, verificando si salta aviso de saldo insuficiente.
        """
        print("Paso 1: Entrando en Casino...")
        self.page.keyboard.press("Escape")
        self.handle_popups()

        # Click en la pestaña de Casino
        casino_tab = self.page.locator(
            "[data-test-id='fdsp-tab-product.casino'] a, [data-test-id='fdsp-tab-product.casino'], a[href*='/casino']:visible"
        ).first
        
        try:
            if casino_tab.is_visible(timeout=2000):
                casino_tab.click(force=True)
            else:
                self.page.goto(f"{self.base_url}/casino", wait_until="domcontentloaded")
        except Exception:
            self.page.goto(f"{self.base_url}/casino", wait_until="domcontentloaded")

        self.page.wait_for_timeout(2500)
        self.handle_popups()

        print("Paso 2: Scrolleando hasta la sección 'Proveedores'...")
        pragmatic_card = self.page.locator(
            "a[href*='proveedores/pragmatic'], a[href*='providers/pragmatic'], img[alt*='Pragmatic' i], [data-test-id*='pragmatic']"
        ).first

        found_provider = False
        for _ in range(15):
            try:
                if pragmatic_card.is_visible(timeout=400):
                    found_provider = True
                    break
            except Exception:
                pass
            self.page.evaluate("window.scrollBy(0, 700)")
            self.page.wait_for_timeout(400)

        print("Paso 3: Click en 'Pragmatic Play'...")
        if found_provider:
            pragmatic_card.scroll_into_view_if_needed()
            self.page.wait_for_timeout(500)
            pragmatic_card.click(force=True)
        else:
            self.page.goto(f"{self.base_url}/casino/proveedores/pragmatic-play", wait_until="domcontentloaded")

        self.page.wait_for_timeout(3000)
        self.handle_popups()

        os.makedirs("evidence", exist_ok=True)
        self.page.screenshot(path="evidence/parte1_pragmatic_lobby.png")
        print("✅ Parte 1 completada: catálogo de Pragmatic Play abierto.")

        # Paso 4: Lanzar el juego y verificar saldo
        print(f"Paso 4: Buscando y abriendo '{game_name}'...")
        game_slug = game_name.lower().replace(" ", "-")
        game_card = self.page.locator(
            f"a[href*='{game_slug}'], [data-test-id*='{game_slug}'], a:has-text('{game_name}')"
        ).first

        for _ in range(5):
            if game_card.is_visible():
                break
            self.page.evaluate("window.scrollBy(0, 500)")
            self.page.wait_for_timeout(400)

        game_card.scroll_into_view_if_needed()
        game_card.click(force=True)
        self.page.wait_for_timeout(1000)

        # Chequeo 1 tras pulsar sobre la tarjeta
        if self.check_insufficient_credits(timeout_ms=1500):
            self.page.screenshot(path="evidence/no_credits_game_card.png")
            raise InsufficientFundsError(f"Saldo insuficiente detectado al pulsar la tarjeta de {game_name}.")

        # Si aparece el botón de confirmación "Jugar" / "Play"
        play_btn = self.page.locator("button:has-text('Jugar'), button:has-text('Play'), a:has-text('Jugar'), a:has-text('Play')").first
        try:
            if play_btn.is_visible(timeout=3000):
                play_btn.click(force=True)
                self.page.wait_for_timeout(1500)
        except Exception:
            pass

        # Chequeo 2 tras confirmar "Jugar"
        if self.check_insufficient_credits(timeout_ms=1500):
            self.page.screenshot(path="evidence/no_credits_play_button.png")
            raise InsufficientFundsError(f"Saldo insuficiente detectado tras hacer clic en 'Jugar' para {game_name}.")

        print(f"Lanzando '{game_name}'...")