import os
import re
import time
from typing import Any, Dict, Optional
from playwright.sync_api import Locator, Page

from src.utils.ocr_helper import parse_numeric_and_currency


class LobbyPage:
    def __init__(self, page: Page, config: Dict[str, Any], evidence_dir: str = "evidence"):
        self.page = page
        self.config = config
        self.base_url = config["url"].rstrip("/")
        self.evidence_dir = evidence_dir

    def _debug_screenshot(self, name: str) -> str:
        os.makedirs(self.evidence_dir, exist_ok=True)
        path = os.path.join(self.evidence_dir, f"debug_{name}.png")
        self.page.screenshot(path=path)
        return path

    def navigate(self):
        """Abre la página principal y descarta pop-ups."""
        self.page.goto(self.base_url, wait_until="domcontentloaded")
        self.page.wait_for_timeout(2000)
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

    def is_logged_in(self) -> bool:
        try:
            return not self.page.locator("[data-test-id='login-button']").first.is_visible(timeout=3000)
        except Exception:
            return False

    def login(self, username: str, password: str):
        """Inicia sesión interactuando como un usuario real (cuenta con o sin saldo)."""
        if not username or not password:
            raise ValueError("Faltan credenciales para el login.")

        self.handle_popups()

        # 1. Click en el botón Iniciar sesión usando data-test-id
        login_btn = self.page.locator("[data-test-id='login-button']").first
        login_btn.wait_for(state="visible", timeout=15000)
        login_btn.click()

        # 2. Esperar a que la página cambie a la pantalla de login o abra el modal
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(2000)

        # 3. Localizar input de usuario / email
        user_input = self.page.locator("input[type='email'], input[type='text'], input[name='username']").first
        try:
            user_input.wait_for(state="visible", timeout=15000)
        except Exception:
            raise RuntimeError("La pantalla de login no muestra inputs.")

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
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(1000)
        self.handle_popups()

        # Fallback por si Enter no dispara el submit:
        try:
            submit_btn = self.page.locator(
                "button[type='submit'], [data-test-id*='login-submit'], [data-test-id*='submit'], "
                "button:has-text('Log in'), button:has-text('Sign in'), button:has-text('Iniciar sesión')"
            ).first
            if submit_btn.is_visible(timeout=1500):
                submit_btn.click(timeout=1500)
        except Exception:
            pass

        # 6. Esperar a que el login se procese y la página vuelva al lobby
        self.page.wait_for_timeout(4000)
        self.handle_popups()

        if not self.is_logged_in():
            self._debug_screenshot("login_failed")
            raise RuntimeError("El login no se completó (el botón de login sigue visible).")

    def _read_balance_text(self) -> Optional[str]:
        # Selectores específicos de saldo visibles en escritorio
        balance_candidates = [
            "user-balance-header:visible",
            "[data-test-id='user-balance']:visible",
            ".amount-money:visible",
            "[data-test-id*='balance']:not(button):visible",
            ".balance-panel:not(.balance-panel-hide) .amount-money:visible",
            # Fallback: cualquier contenedor en el header que muestre la moneda
            "header-brand-secondary-panel span:has-text('€'):visible",
            "header-brand-secondary-panel [class*='amount']:visible"
        ]
        for sel in balance_candidates:
            loc = self.page.locator(sel).first
            try:
                if loc.is_visible(timeout=1500):
                    text = loc.inner_text().strip()
                    if text and any(ch.isdigit() for ch in text):
                        return text
            except Exception:
                continue
        return None

    def _reveal_balance(self):
        """El header puede mostrar solo 'Saldo'/'Balance' con el importe oculto: lo desplegamos."""
        for sel in ["button:has-text('Saldo')", "button:has-text('Balance')",
                    "[data-test-id*='balance'] button", "[data-test-id*='balance-toggle']"]:
            try:
                loc = self.page.locator(sel).first
                if loc.is_visible(timeout=800):
                    loc.click()
                    self.page.wait_for_timeout(800)
                    return
            except Exception:
                continue

    def get_betsson_balance(self, screenshot_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Lee el saldo de Betsson visible en el header tras loguearse.
        Devuelve {"raw_text", "value", "currency"} y guarda una captura del header como evidencia.
        """
        try:
            self.page.locator("[data-test-id='login-button']").first.wait_for(state="hidden", timeout=5000)
        except Exception:
            pass

        text = self._read_balance_text()
        if text is None:
            self._reveal_balance()
            text = self._read_balance_text()

        if screenshot_path:
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            self.page.screenshot(path=screenshot_path, clip={
                "x": 0, "y": 0,
                "width": self.page.viewport_size["width"], "height": 120
            })

        if text is None:
            self._debug_screenshot("balance")
            raise RuntimeError("No se encontró el saldo visible en el header.")

        value, currency = parse_numeric_and_currency(text)
        return {"raw_text": text, "value": value, "currency": currency}

    def refresh_balance(
        self,
        previous_value: float,
        expected_value: Optional[float] = None,
        timeout_sec: int = 45,
        screenshot_path: Optional[str] = None,
        tolerance: float = 0.01
    ) -> Dict[str, Any]:
        """
        Vuelve al lobby y relee el saldo hasta que refleje el resultado del giro
        (el header no siempre se actualiza mientras el juego está abierto).
        """
        self.navigate()
        start = time.time()
        balance = self.get_betsson_balance()
        while time.time() - start < timeout_sec:
            if expected_value is not None and abs(balance["value"] - expected_value) <= tolerance:
                break
            if expected_value is None and abs(balance["value"] - previous_value) > tolerance:
                break
            self.page.wait_for_timeout(3000)
            self.page.reload(wait_until="domcontentloaded")
            self.page.wait_for_timeout(2000)
            self.handle_popups()
            balance = self.get_betsson_balance()
        if screenshot_path:
            balance = self.get_betsson_balance(screenshot_path=screenshot_path)
        return balance

    # ------------------------------------------------------------------
    # Navegación Casino -> Proveedores -> Pragmatic Play -> juego
    # ------------------------------------------------------------------

    def _scroll_content(self, delta_y: int = 700):
        """
        El casino de Betsson hace scroll dentro de un contenedor interno (no en window),
        por eso window.scrollBy no movía nada. La rueda del ratón sobre el contenido sí
        desplaza el contenedor correcto, igual que haría un jugador.
        """
        vw, vh = self.page.viewport_size["width"], self.page.viewport_size["height"]
        self.page.mouse.move(vw * 0.6, vh * 0.65)
        self.page.mouse.wheel(0, delta_y)
        self.page.wait_for_timeout(600)

    def _first_in_viewport(self, locator: Locator, below_y: float = -1) -> Optional[Locator]:
        """Primer elemento visible dentro de la ventana (y opcionalmente por debajo de below_y)."""
        vh = self.page.viewport_size["height"]
        best, best_y = None, None
        try:
            count = min(locator.count(), 25)
        except Exception:
            return None
        for i in range(count):
            el = locator.nth(i)
            try:
                if not el.is_visible():
                    continue
                box = el.bounding_box()
            except Exception:
                continue
            if not box or box["width"] < 5 or box["height"] < 5:
                continue
            center_y = box["y"] + box["height"] / 2
            if 0 < center_y < vh and center_y > below_y and (best_y is None or center_y < best_y):
                best, best_y = el, center_y
        return best

    def _scroll_until_visible(self, locator: Locator, max_scrolls: int = 40, below: Optional[Locator] = None,
                              step: int = 700) -> Optional[Locator]:
        for _ in range(max_scrolls):
            below_y = -1
            if below is not None:
                try:
                    box = below.bounding_box()
                    below_y = box["y"] if box else -1
                except Exception:
                    pass
            el = self._first_in_viewport(locator, below_y)
            if el is not None:
                return el
            self._scroll_content(step)
        return None

    def _step_screenshot(self, name: str):
        os.makedirs(self.evidence_dir, exist_ok=True)
        try:
            self.page.screenshot(path=os.path.join(self.evidence_dir, f"nav_{name}.png"))
        except Exception:
            pass

    def _go_to_casino(self):
        print("Paso 1: Entrando en Casino...")
        self.page.keyboard.press("Escape")
        self.handle_popups()
        casino_tab = self.page.locator(
            "[data-test-id='fdsp-tab-product.casino'] a, [data-test-id='fdsp-tab-product.casino'], "
            "header a:has-text('Casino'):not(:has-text('Vivo')):not(:has-text('Live'))"
        ).first
        try:
            casino_tab.click(timeout=5000)
        except Exception:
            self.page.goto(f"{self._origin()}/casino", wait_until="domcontentloaded")
        self.page.wait_for_timeout(3000)
        self.handle_popups()
        self._step_screenshot("1_casino")

    def _origin(self) -> str:
        # Betsson puede redirigir (p. ej. a otro dominio o idioma): usamos el origen real
        m = re.match(r"^(https?://[^/]+)", self.page.url)
        return m.group(1) if m else self.base_url

    def _open_pragmatic_provider(self) -> bool:
        print("Paso 2: Bajando hasta la sección 'Proveedores'...")
        heading = self.page.get_by_text(re.compile(r"^\s*(proveedores|providers|game providers)\s*$", re.I))
        heading_el = self._scroll_until_visible(heading, max_scrolls=40)
        if heading_el is None:
            print("⚠️ No se encontró el título 'Proveedores'.")
        else:
            print("✅ Sección 'Proveedores' visible.")
            self._scroll_content(250)
        self._step_screenshot("2_proveedores")

        print("Paso 3: Click en 'Pragmatic Play'...")
        provider = self.page.locator(
            "a[href*='pragmatic' i]:not([href*='game' i]):not([href*='juego' i]), "
            "img[alt*='pragmatic' i], [aria-label*='pragmatic' i], [title*='pragmatic' i]"
        )
        # El logo de Pragmatic debe estar en la sección de proveedores (debajo del título),
        # no en las tarjetas de juego que muestran "Pragmatic Play" como proveedor.
        tile = self._scroll_until_visible(provider, max_scrolls=6, below=heading_el, step=300) \
            if heading_el is not None else None
        if tile is not None:
            url_before = self.page.url
            try:
                tile.click(timeout=8000)
                self.page.wait_for_timeout(3000)
                if self.page.url != url_before:
                    print(f"✅ Página de Pragmatic Play abierta: {self.page.url}")
                    self.handle_popups()
                    self._step_screenshot("3_pragmatic")
                    return True
            except Exception as e:
                print(f"⚠️ No se pudo pulsar el logo de Pragmatic: {e}")

        # Respaldo: URL del proveedor según la config
        for path in self.config.get("provider_paths", []):
            url = f"{self._origin()}{path}"
            print(f"Respaldo: abriendo {url}")
            self.page.goto(url, wait_until="domcontentloaded")
            self.page.wait_for_timeout(3000)
            self.handle_popups()
            if "pragmatic" in self.page.url.lower() and self.page.get_by_text(re.compile("pragmatic", re.I)).count():
                self._step_screenshot("3_pragmatic")
                return True
        return False

    def _search_game(self, game_name: str):
        """Último recurso: el buscador 'Buscar juegos' del casino."""
        print(f"Respaldo: buscando '{game_name}' con el buscador del casino...")
        search = self.page.locator(
            "input[type='search'], input[placeholder*='Buscar' i], input[placeholder*='Search' i], "
            "button:has-text('Buscar juegos'), button:has-text('Search games'), :text('Buscar juegos')"
        ).first
        search.click(timeout=8000)
        self.page.wait_for_timeout(800)
        box = self.page.locator("input[type='search'], input[placeholder*='Buscar' i], input[placeholder*='Search' i]").first
        box.fill(game_name, timeout=8000)
        self.page.wait_for_timeout(2500)
        self._step_screenshot("4_busqueda")

    def _game_launched(self, url_before: str, frames_before: int) -> bool:
        """El juego se considera abierto si cambia la URL o aparece un iframe/canvas nuevo."""
        try:
            if self.page.url != url_before:
                return True
            if len(self.page.frames) > frames_before:
                return True
            return any(f.locator("canvas").count() > 0 for f in self.page.frames[1:])
        except Exception:
            return False

    def _wait_game_launched(self, url_before: str, frames_before: int, timeout_sec: int = 15) -> bool:
        start = time.time()
        while time.time() - start < timeout_sec:
            if self._game_launched(url_before, frames_before):
                return True
            self.page.wait_for_timeout(500)
        return False

    def _nearest_in_viewport(self, locator: Locator, x: float, y: float, max_dist: float = 450) -> Optional[Locator]:
        """El elemento visible más cercano al punto (x, y): el 'Jugar' de ESA tarjeta, no de otra."""
        vh = self.page.viewport_size["height"]
        best, best_d = None, None
        try:
            count = min(locator.count(), 40)
        except Exception:
            return None
        for i in range(count):
            el = locator.nth(i)
            try:
                if not el.is_visible():
                    continue
                box = el.bounding_box()
            except Exception:
                continue
            if not box or box["width"] < 3 or not (0 < box["y"] + box["height"] / 2 < vh):
                continue
            d = ((box["x"] + box["width"] / 2 - x) ** 2 + (box["y"] + box["height"] / 2 - y) ** 2) ** 0.5
            if d <= max_dist and (best_d is None or d < best_d):
                best, best_d = el, d
        return best

    def _click_game_tile(self, game_name: str) -> bool:
        """
        Abre cualquier juego por su nombre visible:
          1. Localiza la tarjeta (nombre exacto; si no, que contenga el nombre).
          2. Pasa el ratón por la tarjeta: Betsson muestra 'Jugar' y 'Modo prueba'.
          3. Pulsa el 'Jugar' más cercano a esa tarjeta (Real Play, nunca 'Modo prueba').
          4. Verifica que el juego se abrió (URL nueva o iframe/canvas); si no, click en la tarjeta.
        """
        name = r"\s+".join(re.escape(w) for w in game_name.split())
        candidates = [
            self.page.locator(f"img[alt='{game_name}' i], [title='{game_name}' i], [aria-label='{game_name}' i]")
                .or_(self.page.get_by_text(re.compile(rf"^\s*{name}\s*$", re.I))),
            self.page.get_by_text(re.compile(name, re.I)),
        ]
        el = None
        for i, tile in enumerate(candidates):
            el = self._scroll_until_visible(tile, max_scrolls=25 if i == 0 else 8, step=500)
            if el is not None:
                break
        if el is None:
            return False

        # La tarjeta es el contenedor más cercano que tiene imagen (el nombre suele ir debajo)
        card = el.locator("xpath=ancestor-or-self::*[descendant-or-self::img][1]")
        target = card.first if card.count() else el
        # Centrar la tarjeta: si queda en el borde, el panel 'Jugar' aparece fuera de la pantalla
        try:
            target.evaluate("e => e.scrollIntoView({block: 'center', inline: 'center'})")
            self.page.wait_for_timeout(700)
        except Exception:
            pass
        box = target.bounding_box() or el.bounding_box()
        cx, cy = box["x"] + box["width"] / 2, box["y"] + min(box["height"] / 2, 120)

        url_before, frames_before = self.page.url, len(self.page.frames)
        self.page.mouse.move(cx, cy)
        self.page.wait_for_timeout(1000)
        self._step_screenshot("4_hover_juego")

        play_regex = re.compile(r"^\s*(jugar|jugar ahora|jugar con dinero real|play|play now|real play)\s*$", re.I)
        play = self.page.get_by_role("button", name=play_regex).or_(self.page.get_by_text(play_regex))
        btn = self._nearest_in_viewport(play, cx, cy)
        if btn is not None:
            print("Pulsando 'Jugar' de la tarjeta (Real Play)...")
            btn.click(timeout=8000)
        else:
            print("No apareció 'Jugar' al pasar el ratón: click en la tarjeta.")
            self.page.mouse.click(cx, cy)

        if self._wait_game_launched(url_before, frames_before):
            return True

        # Algunas tarjetas abren un detalle con su propio botón 'Jugar'
        btn = self._first_in_viewport(play)
        if btn is not None:
            btn.click(timeout=8000)
            return self._wait_game_launched(url_before, frames_before)
        return False

    def open_pragmatic_game(self, game_name: Optional[str] = None):
        """
        1. Entrar en la sección Casino.
        2. Bajar (scroll del contenedor interno) hasta la sección 'Proveedores'.
        3. Click en 'Pragmatic Play'.
        4. Seleccionar y lanzar el juego (ej. Gates of Olympus).
        Si un paso falla se usa la URL del proveedor y, por último, el buscador del casino.
        """
        game_name = game_name or self.config["game_name"]
        self._go_to_casino()
        self._open_pragmatic_provider()

        print(f"Paso 4: Buscando y abriendo '{game_name}'...")
        launched = self._click_game_tile(game_name)
        if not launched:
            self._search_game(game_name)
            launched = self._click_game_tile(game_name)
        self._step_screenshot("5_juego")
        if not launched:
            self._debug_screenshot("game_not_found")
            raise RuntimeError(f"No se pudo abrir el juego '{game_name}' (ver capturas nav_*.png).")
        print(f"Lanzando '{game_name}'... ({self.page.url})")
