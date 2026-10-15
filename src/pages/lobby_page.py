import os
from playwright.sync_api import Page, TimeoutError
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

    def login(self):
        """Inicia sesión interactuando como un usuario real en betsson.com."""
        username = os.environ.get("BETSSON_COM_USER")
        password = os.environ.get("BETSSON_COM_PASS")

        if not username or not password:
            raise ValueError("Faltan credenciales: BETSSON_COM_USER o BETSSON_COM_PASS en el entorno (.env).")

        self.handle_popups()

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

        # Cerrar el modal de passkey si aparece
        self.handle_popups()

        # Opcional: si el modal bloquea con overlay o tecla Escape
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(1000)
        self.handle_popups()

        # Fallback por si Enter no dispara el submit:
        try:
            submit_btn = self.page.locator(
                "button[type='submit'], [data-test-id*='login-submit'], [data-test-id*='submit'], button:has-text('Log in'), button:has-text('Sign in')"
            ).first
            if submit_btn.is_visible(timeout=1500):
                submit_btn.click(timeout=1500)
        except Exception:
            pass

        # 6. Esperar a que el login se procese y la página vuelva al lobby
        self.page.wait_for_timeout(4000)
        self.handle_popups()

    def login2(self):
            """Inicia sesión interactuando como un usuario real en betsson.com."""
            username = os.environ.get("BETSSON_NOFUND_USER")
            password = os.environ.get("BETSSON_NOFUND_PASS")
    
            if not username or not password:
                raise ValueError("Faltan credenciales: BETSSON_NOFUND_USER o BETSSON_NOFUND_PASS en el entorno (.env).")
    
            self.handle_popups()
    
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
    
            # Cerrar el modal de passkey si aparece
            self.handle_popups()
    
            # Opcional: si el modal bloquea con overlay o tecla Escape
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(1000)
            self.handle_popups()
    
            # Fallback por si Enter no dispara el submit:
            try:
                submit_btn = self.page.locator(
                    "button[type='submit'], [data-test-id*='login-submit'], [data-test-id*='submit'], button:has-text('Log in'), button:has-text('Sign in')"
                ).first
                if submit_btn.is_visible(timeout=1500):
                    submit_btn.click(timeout=1500)
            except Exception:
                pass
    
            # 6. Esperar a que el login se procese y la página vuelva al lobby
            self.page.wait_for_timeout(4000)
            self.handle_popups()
    
    
    def get_betsson_balance_element(self) -> str:
        """
        Lee el saldo visible en el header tras loguearse.
        Filtra únicamente elementos que estén visibles en pantalla para evitar botones colapsados.
        """
        # Aseguramos que el botón de login ya no esté visible (confirmando que estamos dentro)
        try:
            self.page.locator("[data-test-id='login-button']").first.wait_for(state="hidden", timeout=5000)
        except Exception:
            pass

        # Selectores específicos de saldo visibles en escritorio
        balance_candidates = [
            # Selector específico de texto monetario visible
            "user-balance-header:visible",
            "[data-test-id='user-balance']:visible",
            ".amount-money:visible",
            "[data-test-id*='balance']:not(button):visible",
            ".balance-panel:not(.balance-panel-hide) .amount-money:visible",
            # Fallback: cualquier contenedor en el header que muestre moneda (€ o S/)
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

        # Si aún no lo encuentra por timing, sacamos captura para ver el header real
        os.makedirs("evidence", exist_ok=True)
        self.page.screenshot(path="evidence/debug_balance.png")
        raise RuntimeError("No se encontró el saldo visible en el header. Revisa evidence/debug_balance.png")

    def open_pragmatic_game(self, game_name: str = "Gates of Olympus"):
        """
        1. Entrar en la sección Casino.
        2. Bajar hasta encontrar la sección/carrusel de 'Proveedores'.
        3. Hacer click en 'Pragmatic Play'.
        4. Seleccionar y lanzar el juego (ej. Gates of Olympus).
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
        # Localizador de la tarjeta/logo de Pragmatic Play en la cuadrícula de proveedores
        pragmatic_card = self.page.locator(
            "a[href*='proveedores/pragmatic'], a[href*='providers/pragmatic'], img[alt*='Pragmatic' i], [data-test-id*='pragmatic']"
        ).first

        # Scroll progresivo hacia abajo hasta que el lazy load renderice el bloque de proveedores
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
            # Fallback seguro en caso de que el layout del viewport no lo muestre
            self.page.goto(f"{self.base_url}/casino/proveedores/pragmatic-play", wait_until="domcontentloaded")

        self.page.wait_for_timeout(3000)
        self.handle_popups()

        # Guardar captura que acredita la Parte 1 completada
        os.makedirs("evidence", exist_ok=True)
        self.page.screenshot(path="evidence/parte1_pragmatic_lobby.png")
        print("✅ Parte 1 completada: catálogo de Pragmatic Play abierto.")

        # Paso 4: Lanzar el juego
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
        self.page.wait_for_timeout(1500)

        # Si aparece el botón de confirmación "Jugar" / "Play"
        play_btn = self.page.locator("button:has-text('Jugar'), button:has-text('Play'), a:has-text('Jugar'), a:has-text('Play')").first
        try:
            if play_btn.is_visible(timeout=3000):
                play_btn.click(force=True)
        except Exception:
            pass

        print(f"Lanzando '{game_name}'...")

    def verificar_aviso_sin_saldo(self, screenshot_path: str = "evidence/error_sin_saldo.png") -> bool:
        """
        Espera a que aparezca la advertencia de falta de saldo en el iframe de Pragmatic,
        toma una captura de pantalla como evidencia y retorna si el elemento está visible.
        """
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        
        # 1. Localizador del iframe dentro del Web Component (Shadow DOM)
        frame_promotions = self.page.frame_locator('slots-promotions iframe[title="shadow-root-frame"]')
        
        # 2. Localizador del texto de error de saldo/fondos
        alerta_saldo = frame_promotions.locator("text=/saldo|fondos|insuficiente|balance/i").first
        
        try:
            # Esperar a que el modal sea visible tras el giro
            alerta_saldo.wait_for(state="visible", timeout=12000)
            visible = True
        except TimeoutError:
            visible = False
            
        # 3. Guardar la captura de pantalla como evidencia
        self.page.screenshot(path=screenshot_path)
        
        return visible