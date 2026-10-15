# # import os
# # import time
# # from playwright.sync_api import Page, Locator

# # class GamePage:
# #     def __init__(self, page: Page):
# #         self.page = page
# #         self.canvas_locator: Locator = None

# #     def complete_dgoj_dialogs(self):
# #         """
# #         Resuelve estrictamente la secuencia de los dos modales de la DGOJ:
# #         1. Popup 1 (Aviso): Pulsa 'Iniciar sesión' naranja.
# #         2. Popup 2 (Límites): Selecciona 1 Hora, selecciona 100% (o rellena el input)
# #            y pulsa el botón 'Iniciar sesión' morado.
# #         """
# #         print("Paso 1: Detectando y resolviendo Popup 1 (Aviso DGOJ)...")
# #         # Selector exacto del botón 'Iniciar sesión' naranja del primer modal
# #         popup1_btn = self.page.locator("[data-test-id='start-new-session-buttons-btn-2-button'], [data-test-id='start-new-session-buttons-btn-2']").first
        
# #         try:
# #             if popup1_btn.is_visible(timeout=6000):
# #                 popup1_btn.click(force=True)
# #                 print("Popup 1 confirmado (botón naranja pulsado).")
# #                 self.page.wait_for_timeout(2500)
# #         except Exception as e:
# #             print(f"Aviso en Popup 1: {e}")

# #         print("Paso 2: Detectando y rellenando Popup 2 (Límites de sesión)...")
# #         # Esperamos a que el diálogo o el formulario de límites esté visible
# #         dialog = self.page.locator("dialog[open], [data-test-id='session-settings-form'], [data-test-id='session-settings']").first
# #         try:
# #             dialog.wait_for(state="visible", timeout=10000)
# #             print("Diálogo de límites detectado.")

# #             # 2.1. Seleccionar Tiempo de juego: 1 Hora (3600 segundos)
# #             time_chip = self.page.locator("[data-test-id='session-settings_time-limit-option-3600']").first
# #             time_chip.wait_for(state="visible", timeout=4000)
# #             time_chip.click(force=True)
# #             self.page.wait_for_timeout(400)

# #             # 2.2. Seleccionar Límite de pérdidas: chip 100% o rellenar input
# #             loss_chip = self.page.locator("[data-test-id='session-settings_spending-limit-option-100']").first
# #             if loss_chip.is_visible(timeout=2000):
# #                 loss_chip.click(force=True)
# #                 self.page.wait_for_timeout(400)
# #             else:
# #                 # Si el chip no responde, escribir directamente en el input interno
# #                 loss_input = self.page.locator("input[data-test-id='session-settings_spending-limit-field-input-input']").first
# #                 loss_input.wait_for(state="visible", timeout=2000)
# #                 loss_input.fill("100")
# #                 self.page.wait_for_timeout(400)

# #             # 2.3. Pulsar el botón 'Iniciar sesión' morado del formulario
# #             submit_btn = self.page.locator("[data-test-id='session-settings_submit-button-btn-1-button'], [data-test-id='session-settings_submit-button-btn-1']").first
# #             submit_btn.wait_for(state="visible", timeout=4000)
# #             submit_btn.click(force=True)
# #             print("Formulario de límites enviado con éxito.")

# #             # Esperar a que el backend valide y monte el iframe del juego
# #             self.page.wait_for_timeout(5000)

# #         except Exception as e:
# #             print(f"Error procesando Popup 2: {e}")

# #     def wait_for_game_ready(self, timeout_ms: int = 45000):
# #         """
# #         1. Rellena los dos popups obligatorios.
# #         2. Espera a que el iframe aparezca y el canvas esté listo.
# #         """
# #         self.complete_dgoj_dialogs()

# #         start_time = time.time()
# #         max_seconds = timeout_ms / 1000.0
# #         print("Buscando canvas de Pragmatic Play...")

# #         while (time.time() - start_time) < max_seconds:
# #             # Buscar en todos los frames / iframes
# #             for frame in self.page.frames:
# #                 try:
# #                     canvas = frame.locator("canvas").first
# #                     if canvas.is_visible(timeout=800):
# #                         box = canvas.bounding_box()
# #                         if box and box["width"] > 100 and box["height"] > 100:
# #                             self.canvas_locator = canvas
# #                             print(f"Canvas detectado en frame ({int(box['width'])}x{int(box['height'])})")
# #                             self.page.wait_for_timeout(3000)
# #                             self._dismiss_game_intro()
# #                             return
# #                 except Exception:
# #                     continue

# #             # Buscar en el DOM raíz
# #             try:
# #                 root_canvas = self.page.locator("canvas").first
# #                 if root_canvas.is_visible(timeout=800):
# #                     box = root_canvas.bounding_box()
# #                     if box and box["width"] > 100 and box["height"] > 100:
# #                         self.canvas_locator = root_canvas
# #                         print(f"Canvas detectado en DOM principal ({int(box['width'])}x{int(box['height'])})")
# #                         self.page.wait_for_timeout(3000)
# #                         self._dismiss_game_intro()
# #                         return
# #             except Exception:
# #                 pass

# #             self.page.wait_for_timeout(1000)

# #         os.makedirs("evidence", exist_ok=True)
# #         self.page.screenshot(path="evidence/debug_game_timeout.png")
# #         raise TimeoutError(f"No se encontró el canvas visible tras {timeout_ms}ms. Revisa evidence/debug_game_timeout.png")

# #     def _dismiss_game_intro(self):
# #         """Click al centro para quitar la pantalla de carga de Pragmatic."""
# #         try:
# #             self.click_coordinates(0.5, 0.5)
# #             self.page.wait_for_timeout(1000)
# #         except Exception:
# #             pass

# #     def take_game_screenshot(self, output_path: str = "evidence/test_ready.png") -> str:
# #         if not self.canvas_locator:
# #             self.wait_for_game_ready()
# #         os.makedirs(os.path.dirname(output_path), exist_ok=True)
# #         self.canvas_locator.screenshot(path=output_path)
# #         return output_path

# #     def click_coordinates(self, x_ratio: float, y_ratio: float):
# #         if not self.canvas_locator:
# #             self.wait_for_game_ready()
# #         box = self.canvas_locator.bounding_box()
# #         if not box:
# #             raise RuntimeError("No se pudieron obtener las coordenadas del canvas.")
# #         self.page.mouse.click(box["x"] + (box["width"] * x_ratio), box["y"] + (box["height"] * y_ratio))

# #     def click_spin(self):
# #         print("Pulsando botón Spin en el canvas...")
# #         self.click_coordinates(0.91, 0.86)

# import os
# import time
# from playwright.sync_api import Page, Locator

# class GamePage:
#     def __init__(self, page: Page):
#         self.page = page
#         self.canvas_locator: Locator = None

#     def complete_dgoj_dialogs(self):
#         """
#         Bloquea la ejecución hasta resolver obligatoriamente:
#         1. Popup 1 (Aviso): Clic en 'Iniciar sesión' naranja.
#         2. Popup 2 (Límites DGOJ): Seleccionar tiempo, pérdidas y clic en 'Iniciar sesión' morado.
#         """
#         print("\n==============================================")
#         print("INICIANDO GESTIÓN DE POPUPS DGOJ")
#         print("==============================================")

#         # -------------------------------------------------------------
#         # 1. POPUP 1: Botón naranja "Iniciar sesión"
#         # -------------------------------------------------------------
#         print("Paso 1: Buscando Popup 1 (botón naranja 'Iniciar sesión')...")
#         popup1_clicked = False
#         for _ in range(10):
#             # Intentar click con JS perforando shadow dom
#             popup1_clicked = self.page.evaluate("""() => {
#                 function findDeep(selector, root = document) {
#                     const el = root.querySelector(selector);
#                     if (el) return el;
#                     for (const child of root.querySelectorAll('*')) {
#                         if (child.shadowRoot) {
#                             const found = findDeep(selector, child.shadowRoot);
#                             if (found) return found;
#                         }
#                     }
#                     return null;
#                 }
#                 const btn = findDeep("[data-test-id='start-new-session-buttons-btn-2-button']") ||
#                             findDeep("[data-test-id='start-new-session-buttons-btn-2'] button") ||
#                             findDeep("[data-test-id='start-new-session-buttons-btn-2']");
#                 if (btn) {
#                     btn.click();
#                     return true;
#                 }
#                 return false;
#             }""")
#             if popup1_clicked:
#                 print("✅ POPUP 1: Botón naranja 'Iniciar sesión' pulsado con éxito.")
#                 break
#             self.page.wait_for_timeout(500)

#         if not popup1_clicked:
#             print("⚠️ Popup 1 no encontrado o ya estaba cerrado. Pasando al Popup 2...")

#         # Pausa para que la interfaz monte el segundo diálogo
#         self.page.wait_for_timeout(2000)

#         # -------------------------------------------------------------
#         # 2. POPUP 2: Formulario de límites de sesión
#         # -------------------------------------------------------------
#         print("Paso 2: Esperando a que el Popup 2 (Límites de sesión) esté presente...")
        
#         # Esperamos activamente a que el diálogo exista
#         popup2_ready = False
#         for _ in range(15):
#             has_dialog = self.page.evaluate("""() => {
#                 function findDeep(selector, root = document) {
#                     const el = root.querySelector(selector);
#                     if (el) return el;
#                     for (const child of root.querySelectorAll('*')) {
#                         if (child.shadowRoot) {
#                             const found = findDeep(selector, child.shadowRoot);
#                             if (found) return found;
#                         }
#                     }
#                     return null;
#                 }
#                 return !!findDeep("[data-test-id='session-settings-form']");
#             }""")
#             if has_dialog:
#                 popup2_ready = True
#                 print("✅ POPUP 2: Formulario detectado en pantalla.")
#                 break
#             self.page.wait_for_timeout(500)

#         if not popup2_ready:
#             print("⚠️ No se detectó el formulario del Popup 2 tras esperar. Sacando captura...")
#             os.makedirs("evidence", exist_ok=True)
#             self.page.screenshot(path="evidence/debug_popup2_missing.png")
#             return

#         # Rellenar Popup 2 con JavaScript perforando recursivamente los Shadow Roots
#         print("Rellenando campos de tiempo y créditos en el Popup 2...")
#         filled = self.page.evaluate("""() => {
#             function findDeep(selector, root = document) {
#                 const el = root.querySelector(selector);
#                 if (el) return el;
#                 for (const child of root.querySelectorAll('*')) {
#                     if (child.shadowRoot) {
#                         const found = findDeep(selector, child.shadowRoot);
#                         if (found) return found;
#                     }
#                 }
#                 return null;
#             }

#             // A. Click en tiempo: 1 Hora (3600) o 30 Min (1800)
#             const timeOption = findDeep("[data-test-id='session-settings_time-limit-option-3600'] button") ||
#                                findDeep("[data-test-id='session-settings_time-limit-option-3600']") ||
#                                findDeep("[data-test-id='session-settings_time-limit-option-1800'] button") ||
#                                findDeep("[data-test-id='session-settings_time-limit-option-1800']");
#             if (timeOption) timeOption.click();

#             // B. Rellenar input de límite de pérdidas o seleccionar chip
#             const lossInput = findDeep("#session-settings_spending-limit-field-input-input") ||
#                               findDeep("input[data-test-id='session-settings_spending-limit-field-input-input']");
#             if (lossInput) {
#                 lossInput.value = '100';
#                 lossInput.dispatchEvent(new Event('input', { bubbles: true }));
#                 lossInput.dispatchEvent(new Event('change', { bubbles: true }));
#             }

#             const lossChip = findDeep("[data-test-id='session-settings_spending-limit-option-100'] button") ||
#                              findDeep("[data-test-id='session-settings_spending-limit-option-100']");
#             if (lossChip) lossChip.click();

#             // C. Pulsar el botón 'Iniciar sesión' morado
#             const submitBtn = findDeep("[data-test-id='session-settings_submit-button-btn-1-button']") ||
#                               findDeep("[data-test-id='session-settings_submit-button-btn-1'] button") ||
#                               findDeep("[data-test-id='session-settings_submit-button-btn-1']");
#             if (submitBtn) {
#                 submitBtn.click();
#                 return "COMPLETADO";
#             }
#             return "SUBMIT_NO_ENCONTRADO";
#         }""")

#         print(f"Resultado del relleno de Popup 2: {filled}")
#         print("Esperando 5 segundos a que la DGOJ registre la sesión y desaparezca el modal...")
#         self.page.wait_for_timeout(5000)
#         print("==============================================\n")

#     def wait_for_game_ready(self, timeout_ms: int = 45000):
#         """
#         Primero ejecuta obligatoriamente la resolución de popups.
#         Solo después busca el canvas en iframes o DOM principal.
#         """
#         # Ejecutar la secuencia de popups
#         self.complete_dgoj_dialogs()

#         start_time = time.time()
#         max_seconds = timeout_ms / 1000.0
#         print("Buscando canvas de Pragmatic Play en iframes...")

#         while (time.time() - start_time) < max_seconds:
#             # Buscar en todos los iframes anidados
#             for frame in self.page.frames:
#                 try:
#                     canvas = frame.locator("canvas").first
#                     if canvas.is_visible(timeout=800):
#                         box = canvas.bounding_box()
#                         if box and box["width"] > 100 and box["height"] > 100:
#                             self.canvas_locator = canvas
#                             print(f"Canvas detectado en frame: {frame.url[:50]}... ({int(box['width'])}x{int(box['height'])})")
#                             self.page.wait_for_timeout(3000)
#                             self._dismiss_game_intro()
#                             return
#                 except Exception:
#                     continue

#             # Buscar en el documento principal
#             try:
#                 root_canvas = self.page.locator("canvas").first
#                 if root_canvas.is_visible(timeout=800):
#                     box = root_canvas.bounding_box()
#                     if box and box["width"] > 100 and box["height"] > 100:
#                         self.canvas_locator = root_canvas
#                         print(f"Canvas detectado en DOM principal ({int(box['width'])}x{int(box['height'])})")
#                         self.page.wait_for_timeout(3000)
#                         self._dismiss_game_intro()
#                         return
#             except Exception:
#                 pass

#             self.page.wait_for_timeout(1000)

#         os.makedirs("evidence", exist_ok=True)
#         self.page.screenshot(path="evidence/debug_game_timeout.png")
#         raise TimeoutError(f"No se encontró el canvas visible tras {timeout_ms}ms. Revisa evidence/debug_game_timeout.png")

#     def _dismiss_game_intro(self):
#         """Click al centro para quitar la pantalla de carga de Pragmatic."""
#         try:
#             self.click_coordinates(0.5, 0.5)
#             self.page.wait_for_timeout(1000)
#         except Exception:
#             pass

#     def take_game_screenshot(self, output_path: str = "evidence/test_ready.png") -> str:
#         if not self.canvas_locator:
#             self.wait_for_game_ready()
#         os.makedirs(os.path.dirname(output_path), exist_ok=True)
#         self.canvas_locator.screenshot(path=output_path)
#         return output_path

#     def click_coordinates(self, x_ratio: float, y_ratio: float):
#         if not self.canvas_locator:
#             self.wait_for_game_ready()
#         box = self.canvas_locator.bounding_box()
#         if not box:
#             raise RuntimeError("No se pudieron obtener las coordenadas del canvas.")
#         self.page.mouse.click(box["x"] + (box["width"] * x_ratio), box["y"] + (box["height"] * y_ratio))

#     def click_spin(self):
#         print("Pulsando botón Spin en el canvas...")
#         self.click_coordinates(0.91, 0.86)


import os
import time
from playwright.sync_api import Page, Locator


class InsufficientFundsError(Exception):
    """Excepción lanzada cuando el usuario no tiene fondos/créditos suficientes para jugar."""
    pass


class GamePage:
    def __init__(self, page: Page):
        self.page = page
        self.canvas_locator: Locator = None

    def check_insufficient_credits(self, timeout_ms: int = 1500) -> bool:
        """
        Detecta si aparece el banner o modal indicando falta de saldo/créditos.
        Busca tanto en el DOM principal (con Shadow DOM) como en iframes.
        """
        # 1. Comprobación vía selectores / texto en DOM principal e iframes
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

        # Chequeo rápido con locator en la página raíz
        try:
            banner = self.page.locator(selector_query).first
            if banner.is_visible(timeout=timeout_ms):
                print("⚠️ Banner de falta de fondos detectado por selector data-test-id/clase.")
                return True
        except Exception:
            pass

        # Chequeo por texto visible en la página
        for pattern in text_patterns:
            try:
                locator = self.page.locator(f"text=/{pattern}/i").first
                if locator.is_visible(timeout=200):
                    print(f"⚠️ Aviso de falta de saldo detectado por texto: '{pattern}'")
                    return True
            except Exception:
                pass

        # 2. Búsqueda profunda en Shadow DOM y contenedores dinámicos
        has_banner_js = self.page.evaluate("""() => {
            const keywords = [
                'saldo insuficiente', 'sin saldo', 'no tienes saldo',
                'fondos insuficientes', 'no tienes créditos', 'créditos insuficientes',
                'insufficient funds', 'insufficient balance', 'depositar'
            ];

            function searchNodes(root = document) {
                // Revisar elementos de alerta/banner
                const candidates = root.querySelectorAll("[role='alert'], [data-test-id*='balance'], [data-test-id*='deposit'], [class*='banner'], [class*='modal']");
                for (const el of candidates) {
                    const text = (el.innerText || el.textContent || '').toLowerCase();
                    if (keywords.some(kw => text.includes(kw))) {
                        return true;
                    }
                }

                // Perforar Shadow DOM
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

        self.page.wait_for_timeout(2000)

        # -------------------------------------------------------------
        # 2. POPUP 2: Formulario de límites de sesión
        # -------------------------------------------------------------
        print("Paso 2: Esperando a que el Popup 2 (Límites de sesión) esté presente...")
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
        1. Resuelve los popups DGOJ.
        2. Revisa si hay banner de falta de créditos antes de continuar.
        3. Espera a que el canvas esté disponible.
        """
        self.complete_dgoj_dialogs()

        # Comprobación de saldo tras confirmar límites
        if self.check_insufficient_credits(timeout_ms=1000):
            os.makedirs("evidence", exist_ok=True)
            self.page.screenshot(path="evidence/no_credits_detected.png")
            raise InsufficientFundsError("Se detectó el banner de créditos insuficientes tras configurar la sesión.")

        start_time = time.time()
        max_seconds = timeout_ms / 1000.0
        print("Buscando canvas de Pragmatic Play en iframes...")

        while (time.time() - start_time) < max_seconds:
            # Chequeo reactivo durante el bucle de espera por si el banner salta tarde
            if self.check_insufficient_credits(timeout_ms=300):
                os.makedirs("evidence", exist_ok=True)
                self.page.screenshot(path="evidence/no_credits_detected.png")
                raise InsufficientFundsError("Banner de créditos insuficientes detectado mientras se esperaba el juego.")

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
        """Pulsa el botón Spin y valida que no aparezca el aviso de falta de saldo."""
        print("Pulsando botón Spin en el canvas...")
        self.click_coordinates(0.91, 0.86)
        self.page.wait_for_timeout(1000)

        if self.check_insufficient_credits(timeout_ms=1000):
            os.makedirs("evidence", exist_ok=True)
            self.page.screenshot(path="evidence/no_credits_after_spin.png")
            raise InsufficientFundsError("Apareció el aviso de fondos insuficientes tras pulsar Spin.")