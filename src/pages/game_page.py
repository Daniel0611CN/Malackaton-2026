import os
import time
from playwright.sync_api import Page, Locator

class GamePage:
    def __init__(self, page: Page):
        self.page = page
        self.canvas_locator: Locator = None

    def complete_dgoj_dialogs(self):
        """
        Bloquea la ejecución hasta resolver obligatoriamente:
        1. Popup 1 (Aviso): Clic en 'Iniciar sesión' naranja.
        2. Popup 2 (Límites DGOJ): Seleccionar tiempo, pérdidas y clic en 'Iniciar sesión' morado.
        """
        print("\n==============================================")
        print("INICIANDO GESTIÓN DE POPUPS DGOJ")
        print("==============================================")

        # -------------------------------------------------------------
        # 1. POPUP 1: Botón naranja "Iniciar sesión"
        # -------------------------------------------------------------
        print("Paso 1: Buscando Popup 1 (botón naranja 'Iniciar sesión')...")
        popup1_clicked = False
        for _ in range(10):
            # Intentar click con JS perforando shadow dom
            popup1_clicked = self.page.evaluate("""() => {
                function findDeep(selector, root = document) {
                    const el = root.querySelector(selector);
                    if (el) return el;
                    for (const child of root.querySelectorAll('*')) {
                        if (child.shadowRoot) {
                            const found = findDeep(selector, child.shadowRoot);
                            if (found) return found;
                        }
                    }
                    return null;
                }
                const btn = findDeep("[data-test-id='start-new-session-buttons-btn-2-button']") ||
                            findDeep("[data-test-id='start-new-session-buttons-btn-2'] button") ||
                            findDeep("[data-test-id='start-new-session-buttons-btn-2']");
                if (btn) {
                    btn.click();
                    return true;
                }
                return false;
            }""")
            if popup1_clicked:
                print("✅ POPUP 1: Botón naranja 'Iniciar sesión' pulsado con éxito.")
                break
            self.page.wait_for_timeout(500)

        if not popup1_clicked:
            print("⚠️ Popup 1 no encontrado o ya estaba cerrado. Pasando al Popup 2...")

        # Pausa para que la interfaz monte el segundo diálogo
        self.page.wait_for_timeout(2000)

        # -------------------------------------------------------------
        # 2. POPUP 2: Formulario de límites de sesión
        # -------------------------------------------------------------
        print("Paso 2: Esperando a que el Popup 2 (Límites de sesión) esté presente...")
        
        # Esperamos activamente a que el diálogo exista
        popup2_ready = False
        for _ in range(15):
            has_dialog = self.page.evaluate("""() => {
                function findDeep(selector, root = document) {
                    const el = root.querySelector(selector);
                    if (el) return el;
                    for (const child of root.querySelectorAll('*')) {
                        if (child.shadowRoot) {
                            const found = findDeep(selector, child.shadowRoot);
                            if (found) return found;
                        }
                    }
                    return null;
                }
                return !!findDeep("[data-test-id='session-settings-form']");
            }""")
            if has_dialog:
                popup2_ready = True
                print("✅ POPUP 2: Formulario detectado en pantalla.")
                break
            self.page.wait_for_timeout(500)

        if not popup2_ready:
            print("⚠️ No se detectó el formulario del Popup 2 tras esperar. Sacando captura...")
            os.makedirs("evidence", exist_ok=True)
            self.page.screenshot(path="evidence/debug_popup2_missing.png")
            return

        # Rellenar Popup 2 con JavaScript perforando recursivamente los Shadow Roots
        print("Rellenando campos de tiempo y créditos en el Popup 2...")
        filled = self.page.evaluate("""() => {
            function findDeep(selector, root = document) {
                const el = root.querySelector(selector);
                if (el) return el;
                for (const child of root.querySelectorAll('*')) {
                    if (child.shadowRoot) {
                        const found = findDeep(selector, child.shadowRoot);
                        if (found) return found;
                    }
                }
                return null;
            }

            // A. Click en tiempo: 1 Hora (3600) o 30 Min (1800)
            const timeOption = findDeep("[data-test-id='session-settings_time-limit-option-3600'] button") ||
                               findDeep("[data-test-id='session-settings_time-limit-option-3600']") ||
                               findDeep("[data-test-id='session-settings_time-limit-option-1800'] button") ||
                               findDeep("[data-test-id='session-settings_time-limit-option-1800']");
            if (timeOption) timeOption.click();

            // B. Rellenar input de límite de pérdidas o seleccionar chip
            const lossInput = findDeep("#session-settings_spending-limit-field-input-input") ||
                              findDeep("input[data-test-id='session-settings_spending-limit-field-input-input']");
            if (lossInput) {
                lossInput.value = '100';
                lossInput.dispatchEvent(new Event('input', { bubbles: true }));
                lossInput.dispatchEvent(new Event('change', { bubbles: true }));
            }

            const lossChip = findDeep("[data-test-id='session-settings_spending-limit-option-100'] button") ||
                             findDeep("[data-test-id='session-settings_spending-limit-option-100']");
            if (lossChip) lossChip.click();

            // C. Pulsar el botón 'Iniciar sesión' morado
            const submitBtn = findDeep("[data-test-id='session-settings_submit-button-btn-1-button']") ||
                              findDeep("[data-test-id='session-settings_submit-button-btn-1'] button") ||
                              findDeep("[data-test-id='session-settings_submit-button-btn-1']");
            if (submitBtn) {
                submitBtn.click();
                return "COMPLETADO";
            }
            return "SUBMIT_NO_ENCONTRADO";
        }""")

        print(f"Resultado del relleno de Popup 2: {filled}")
        print("Esperando 5 segundos a que la DGOJ registre la sesión y desaparezca el modal...")
        self.page.wait_for_timeout(5000)
        print("==============================================\n")

    def wait_for_game_ready(self, timeout_ms: int = 45000):
        """
        Primero ejecuta obligatoriamente la resolución de popups.
        Solo después busca el canvas en iframes o DOM principal.
        """
        # Ejecutar la secuencia de popups
        self.complete_dgoj_dialogs()

        start_time = time.time()
        max_seconds = timeout_ms / 1000.0
        print("Buscando canvas de Pragmatic Play en iframes...")

        while (time.time() - start_time) < max_seconds:
            # Buscar en todos los iframes anidados
            for frame in self.page.frames:
                try:
                    canvas = frame.locator("canvas").first
                    if canvas.is_visible(timeout=800):
                        box = canvas.bounding_box()
                        if box and box["width"] > 100 and box["height"] > 100:
                            self.canvas_locator = canvas
                            print(f"Canvas detectado en frame: {frame.url[:50]}... ({int(box['width'])}x{int(box['height'])})")
                            self.page.wait_for_timeout(3000)
                            self._dismiss_game_intro()
                            return
                except Exception:
                    continue

            # Buscar en el documento principal
            try:
                root_canvas = self.page.locator("canvas").first
                if root_canvas.is_visible(timeout=800):
                    box = root_canvas.bounding_box()
                    if box and box["width"] > 100 and box["height"] > 100:
                        self.canvas_locator = root_canvas
                        print(f"Canvas detectado en DOM principal ({int(box['width'])}x{int(box['height'])})")
                        self.page.wait_for_timeout(3000)
                        self._dismiss_game_intro()
                        return
            except Exception:
                pass

            self.page.wait_for_timeout(1000)

        os.makedirs("evidence", exist_ok=True)
        self.page.screenshot(path="evidence/debug_game_timeout.png")
        raise TimeoutError(f"No se encontró el canvas visible tras {timeout_ms}ms. Revisa evidence/debug_game_timeout.png")

    def _dismiss_game_intro(self):
        """Click al centro para quitar la pantalla de carga de Pragmatic."""
        try:
            self.click_coordinates(0.5, 0.5)
            self.page.wait_for_timeout(1000)
        except Exception:
            pass

    def take_game_screenshot(self, output_path: str = "evidence/test_ready.png") -> str:
        if not self.canvas_locator:
            self.wait_for_game_ready()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self.canvas_locator.screenshot(path=output_path)
        return output_path

    def click_coordinates(self, x_ratio: float, y_ratio: float):
        if not self.canvas_locator:
            self.wait_for_game_ready()
        box = self.canvas_locator.bounding_box()
        if not box:
            raise RuntimeError("No se pudieron obtener las coordenadas del canvas.")
        self.page.mouse.click(box["x"] + (box["width"] * x_ratio), box["y"] + (box["height"] * y_ratio))

    def click_spin(self):
        print("Pulsando botón Spin en el canvas...")
        self.click_coordinates(0.91, 0.86)

    def verify_insufficient_funds_modal(self, screenshot_path: str = "evidence/test_sin_saldo.png", timeout_sec: int = 12) -> bool:
        """
        Espera a que aparezca la advertencia de falta de saldo.
        Verifica tanto el Shadow DOM de slots-promotions como posibles overlays en iframes o página raíz.
        Toma una captura de pantalla completa como evidencia y retorna True si lo detectó.
        """
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        print("Esperando modal/aviso de saldo insuficiente...")

        regex_texto = r"/saldo|fondos|insuficiente|balance|funds|no tienes/i"
        detected = False
        start = time.time()

        while (time.time() - start) < timeout_sec:
            # 1. Estrategia A: Shadow DOM estándar de slots-promotions (en root o frames)
            try:
                # Comprobar en page principal
                promo_frame = self.page.frame_locator('slots-promotions iframe[title="shadow-root-frame"]')
                alerta = promo_frame.locator(f"text={regex_texto}").first
                if alerta.is_visible(timeout=500):
                    print("✅ Aviso detectado en slots-promotions (Shadow DOM raíz).")
                    detected = True
                    break
            except Exception:
                pass

            # 2. Estrategia B: Buscar en los sub-iframes del juego (donde corre Pragmatic)
            for frame in self.page.frames:
                try:
                    # En el propio frame
                    loc = frame.locator(f"text={regex_texto}").first
                    if loc.is_visible(timeout=300):
                        print(f"✅ Aviso detectado en frame: {frame.url[:45]}...")
                        detected = True
                        break

                    # O en slots-promotions dentro de ese frame
                    nested_promo = frame.frame_locator('slots-promotions iframe[title="shadow-root-frame"]')
                    nested_loc = nested_promo.locator(f"text={regex_texto}").first
                    if nested_loc.is_visible(timeout=300):
                        print("✅ Aviso detectado en slots-promotions anidado en iframe.")
                        detected = True
                        break
                except Exception:
                    continue

            if detected:
                break

            self.page.wait_for_timeout(600)

        # Captura de pantalla de la ventana completa para evidencia
        self.page.screenshot(path=screenshot_path, full_page=False)
        print(f"Captura guardada en: {screenshot_path}")

        if not detected:
            print("⚠️ No se detectó texto de saldo insuficiente tras el timeout.")

        return detected