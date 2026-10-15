import os
import re
import time
from typing import Any, Dict, Optional
from playwright.sync_api import Page, Locator

from src.utils.ocr_helper import read_game_hud, read_screen_text, find_keywords
from src.utils.vision_helper import locate_spin_button, frame_change_ratio

PRACTICE_BANNER_REGEX = r"/modo pr[aá]ctica|practice mode|play for fun|modo demo/i"
REAL_PLAY_LINK_REGEX = r"/jugar en modo real|play for real|real money|dinero real/i"


class GamePage:
    def __init__(self, page: Page, config: Optional[Dict[str, Any]] = None, evidence_dir: str = "evidence",
                 spin_threshold: float = 0.55):
        self.page = page
        self.config = config or {}
        self.evidence_dir = evidence_dir
        self.spin_threshold = spin_threshold
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
            self._debug_screenshot("popup2_missing")
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

    def wait_for_game_ready(self, timeout_ms: int = 60000):
        """
        Primero ejecuta obligatoriamente la resolución de popups.
        Después se asegura de estar en Real Play y busca el canvas en iframes o DOM principal.
        """
        self.complete_dgoj_dialogs()
        self.ensure_real_play()
        self._find_canvas(timeout_ms)
        self.page.wait_for_timeout(3000)
        self._dismiss_game_intro()

    def _find_canvas(self, timeout_ms: int):
        start_time = time.time()
        print("Buscando canvas de Pragmatic Play en iframes...")

        while (time.time() - start_time) < timeout_ms / 1000.0:
            # Buscar en todos los iframes anidados y en el documento principal
            for frame in self.page.frames:
                try:
                    canvas = frame.locator("canvas").first
                    if canvas.is_visible(timeout=800):
                        box = canvas.bounding_box()
                        if box and box["width"] > 100 and box["height"] > 100:
                            self.canvas_locator = canvas
                            print(f"Canvas detectado en frame: {frame.url[:50]}... ({int(box['width'])}x{int(box['height'])})")
                            return
                except Exception:
                    continue
            self.page.wait_for_timeout(1000)

        self._debug_screenshot("game_timeout")
        raise TimeoutError(f"No se encontró el canvas visible tras {timeout_ms}ms.")

    def is_practice_mode(self) -> bool:
        """Betsson muestra un banner 'Estás jugando ... en el modo Práctica' cuando no es Real Play."""
        for frame in self.page.frames:
            try:
                if frame.locator(f"text={PRACTICE_BANNER_REGEX}").first.is_visible(timeout=300):
                    return True
            except Exception:
                continue
        return False

    def ensure_real_play(self):
        """Si el juego se abrió en modo práctica/demo, pulsa 'Quiero jugar en modo real' / 'Play for real'."""
        for _ in range(3):
            if not self.is_practice_mode():
                return
            print("El juego está en modo Práctica: cambiando a Real Play...")
            for frame in self.page.frames:
                try:
                    link = frame.locator(f"text={REAL_PLAY_LINK_REGEX}").first
                    if link.is_visible(timeout=500):
                        link.click()
                        self.page.wait_for_timeout(5000)
                        self.complete_dgoj_dialogs()
                        self.canvas_locator = None
                        break
                except Exception:
                    continue

    def _dismiss_game_intro(self):
        """
        Pantalla de bienvenida de Pragmatic: busca el botón de flechas por template matching;
        si no aparece, hace click en el centro.
        """
        # Ojo: el botón Spin del juego usa las mismas flechas que el de la intro. Solo se pulsa
        # si el HUD (crédito/apuesta) aún no es visible; si no, lanzaríamos un giro no contabilizado.
        for attempt in range(3):
            path = os.path.join(self.evidence_dir, f"game_intro_{attempt}.png")
            try:
                self.take_game_screenshot(path)
                hud = read_game_hud(path, labels=self.config.get("hud_labels"))
                if hud["credit"] is not None or hud["bet"] is not None:
                    return
                coords = locate_spin_button(path, threshold=self.spin_threshold)
                if coords:
                    self.click_canvas_pixel(*coords)
                else:
                    self.click_coordinates(0.5, 0.5)
                self.page.wait_for_timeout(2500)
            except Exception as e:
                print(f"[INTRO] No se pudo descartar la intro: {e}")
                return

    def _debug_screenshot(self, name: str) -> str:
        os.makedirs(self.evidence_dir, exist_ok=True)
        path = os.path.join(self.evidence_dir, f"debug_{name}.png")
        self.page.screenshot(path=path)
        return path

    def take_game_screenshot(self, output_path: str) -> str:
        """Captura solo el canvas del juego (lo que el jugador ve dentro del iframe)."""
        if not self.canvas_locator:
            self.wait_for_game_ready()
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        self.canvas_locator.screenshot(path=output_path)
        return output_path

    def take_page_screenshot(self, output_path: str) -> str:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        self.page.screenshot(path=output_path)
        return output_path

    def click_coordinates(self, x_ratio: float, y_ratio: float):
        if not self.canvas_locator:
            self.wait_for_game_ready()
        box = self.canvas_locator.bounding_box()
        if not box:
            raise RuntimeError("No se pudieron obtener las coordenadas del canvas.")
        self.page.mouse.click(box["x"] + (box["width"] * x_ratio), box["y"] + (box["height"] * y_ratio))

    def click_canvas_pixel(self, x: int, y: int):
        """Click en un píxel de la captura del canvas (la captura está en px CSS, scale=1)."""
        box = self.canvas_locator.bounding_box()
        self.page.mouse.click(box["x"] + x, box["y"] + y)

    def read_hud(self, screenshot_path: str) -> Dict[str, Any]:
        """OCR del HUD del juego: crédito, apuesta, ganancia y divisa visibles."""
        hud = read_game_hud(screenshot_path, labels=self.config.get("hud_labels"))
        print(f"[HUD] {screenshot_path}: crédito={hud['credit']} apuesta={hud['bet']} "
              f"ganancia={hud['win']} divisa={hud['currency']} | '{hud['raw_text']}'")
        return hud

    def read_hud_stable(self, prefix: str, attempts: int = 4) -> Dict[str, Any]:
        """Lee el HUD hasta obtener dos lecturas consecutivas iguales (los contadores de premio se animan)."""
        previous, hud, path = None, None, None
        for i in range(attempts):
            path = self.take_game_screenshot(f"{prefix}_{i}.png")
            hud = self.read_hud(path)
            if previous and hud["credit"] is not None and hud["credit"] == previous["credit"] \
                    and hud["bet"] == previous["bet"]:
                break
            previous = hud
            self.page.wait_for_timeout(1500)
        hud["screenshot"] = path
        return hud

    def click_spin(self, screenshot_path: str) -> Dict[str, Any]:
        """
        Localiza el botón Spin en la captura actual por template matching y lo pulsa.
        Si la visión no lo encuentra, usa la posición relativa conocida como último recurso.
        """
        coords = locate_spin_button(screenshot_path, threshold=self.spin_threshold)
        if coords:
            print(f"Pulsando Spin detectado por visión en {coords}...")
            self.click_canvas_pixel(*coords)
            return {"method": "template_matching", "coords": coords}
        print("Spin no localizado por visión: usando posición relativa de respaldo.")
        self.click_coordinates(0.91, 0.86)
        return {"method": "fallback_ratio", "coords": None}

    def measure_idle_motion(self, prefix: str) -> float:
        """Mide la animación ambiental del juego en reposo para calibrar los umbrales de movimiento."""
        a = self.take_game_screenshot(f"{prefix}_idle_a.png")
        self.page.wait_for_timeout(700)
        b = self.take_game_screenshot(f"{prefix}_idle_b.png")
        return frame_change_ratio(a, b)

    def observe_spin(self, before_path: str, frames_dir: str, idle_motion: float = 0.0,
                     timeout_sec: int = 60) -> Dict[str, Any]:
        """
        Observa el canvas tras pulsar Spin y decide, solo con lo que se ve en pantalla:
          - started:   la zona de rodillos cambia muy por encima de la animación de reposo.
          - completed: tras empezar, varios fotogramas consecutivos vuelven a estar quietos.
        """
        os.makedirs(frames_dir, exist_ok=True)
        start_threshold = max(0.03, idle_motion * 2.5 + 0.01)
        stable_threshold = max(0.015, idle_motion * 1.5 + 0.005)

        frames, ratios_vs_before, ratios_vs_prev = [], [], []
        started_index, stable_count, completed = None, 0, False
        prev = before_path
        t0 = time.time()
        i = 0
        while time.time() - t0 < timeout_sec:
            self.page.wait_for_timeout(600)
            path = self.take_game_screenshot(os.path.join(frames_dir, f"frame_{i:03d}.png"))
            r_before = frame_change_ratio(before_path, path)
            r_prev = frame_change_ratio(prev, path)
            frames.append(path)
            ratios_vs_before.append(round(r_before, 4))
            ratios_vs_prev.append(round(r_prev, 4))

            if started_index is None and max(r_before, r_prev) >= start_threshold:
                started_index = i
            elif started_index is not None:
                stable_count = stable_count + 1 if r_prev <= stable_threshold else 0
                if stable_count >= 3:
                    completed = True
                    break
            if started_index is None and time.time() - t0 > 10:
                break
            prev = path
            i += 1

        result = {
            "started": started_index is not None,
            "completed": completed,
            "first_moving_frame": frames[started_index] if started_index is not None else None,
            "last_frame": frames[-1] if frames else None,
            "frames": frames,
            "ratios_vs_before": ratios_vs_before,
            "ratios_vs_prev": ratios_vs_prev,
            "start_threshold": round(start_threshold, 4),
            "stable_threshold": round(stable_threshold, 4),
            "duration_sec": round(time.time() - t0, 1),
        }
        print(f"[SPIN] started={result['started']} completed={result['completed']} "
              f"duración={result['duration_sec']}s umbrales={start_threshold:.3f}/{stable_threshold:.3f}")
        return result

    def _dom_text_matches(self, keywords) -> Optional[str]:
        """Busca el mensaje en el DOM visible (overlays de Betsson o iframes accesibles)."""
        pattern = "|".join(re.escape(k) for k in keywords)
        selectors = [f"text=/{pattern}/i"]
        for frame in self.page.frames:
            for sel in selectors:
                try:
                    loc = frame.locator(sel).first
                    if loc.is_visible(timeout=300):
                        return loc.inner_text(timeout=1000).strip()
                except Exception:
                    continue
            try:
                promo = frame.frame_locator('slots-promotions iframe[title="shadow-root-frame"]')
                loc = promo.locator(selectors[0]).first
                if loc.is_visible(timeout=300):
                    return loc.inner_text(timeout=1000).strip()
            except Exception:
                continue
        return None

    def wait_for_insufficient_funds_message(self, keywords, screenshot_prefix: str,
                                            timeout_sec: int = 20) -> Dict[str, Any]:
        """
        Espera el aviso de saldo insuficiente tal y como lo ve el jugador:
          1. OCR de la captura de la página completa (el aviso puede estar dentro del canvas
             del proveedor o en un overlay de Betsson).
          2. Como apoyo, texto visible en el DOM accesible.
        """
        start = time.time()
        attempt = 0
        result = {"detected": False, "source": None, "text": "", "screenshot": None}
        while time.time() - start < timeout_sec:
            path = self.take_page_screenshot(f"{screenshot_prefix}_{attempt}.png")
            screen_text = read_screen_text(path)
            found = find_keywords(screen_text, keywords)
            result.update({"screenshot": path, "text": screen_text})
            if found:
                result.update({"detected": True, "source": "ocr", "keywords": found})
                break
            dom_text = self._dom_text_matches(keywords)
            if dom_text:
                result.update({"detected": True, "source": "dom", "text": dom_text,
                               "keywords": find_keywords(dom_text, keywords)})
                break
            attempt += 1
            self.page.wait_for_timeout(1500)
        print(f"[SALDO INSUFICIENTE] detectado={result['detected']} fuente={result['source']}")
        return result
