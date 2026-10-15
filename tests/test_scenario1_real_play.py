"""
Escenario 1 — Completed Real Play spin.

Todo lo que se verifica sale de lo que el jugador ve: saldo del header de Betsson, HUD del
juego leído por OCR, botón Spin localizado por template matching y movimiento de rodillos
medido por diferencia entre fotogramas del canvas.
"""
import os

from src.pages.game_page import GamePage
from src.utils.math_checker import validate_spin_scenario
from src.utils.ocr_helper import find_amounts_on_screen

TOLERANCE = 0.01


def _close(a, b):
    return a is not None and b is not None and abs(a - b) <= TOLERANCE


def _determine_payout(hud_after, credit_before, credit_after, wager, frames):
    """
    Premio observado en pantalla:
      1. Campo WIN/GANANCIA del HUD si aparece.
      2. Si el crédito bajó exactamente la apuesta, no hubo premio.
      3. Si no, se busca en los últimos fotogramas un importe igual al premio implícito.
    """
    if hud_after.get("win"):
        return hud_after["win"], "campo WIN/GANANCIA del HUD"
    if None in (credit_before, credit_after, wager):
        return 0.0, "no determinable (lectura de HUD incompleta)"
    implied = round(credit_after - credit_before + wager, 2)
    if abs(implied) <= TOLERANCE:
        return 0.0, "sin premio (el crédito bajó exactamente la apuesta)"
    for frame in reversed(frames[-4:]):
        if any(_close(v, implied) for v in find_amounts_on_screen(frame)):
            return implied, f"importe de premio visible en {os.path.basename(frame)}"
    return 0.0, f"no se vio en pantalla un premio de {implied:.2f}"


def test_scenario_1_real_play_spin(market_config, open_session, scenario_report):
    cfg = market_config
    currency = cfg["currency"]
    report = scenario_report("scenario1_real_play", "Escenario 1 · Real Play spin completado")
    ev = report.evidence_dir
    page = None

    try:
        page, lobby = open_session("funded", ev)

        # 1-2. Lobby autenticado y saldo de Betsson antes del giro
        betsson_before = lobby.get_betsson_balance(screenshot_path=f"{ev}/01_betsson_balance_before.png")
        report.add_evidence("Saldo Betsson antes del giro", f"{ev}/01_betsson_balance_before.png")
        report.data["betsson_before"] = betsson_before

        # 3. Lanzar juego de Pragmatic Play en Real Play
        lobby.open_pragmatic_game()
        game = GamePage(page, cfg, ev)
        game.wait_for_game_ready()
        loaded = game.take_page_screenshot(f"{ev}/02_game_loaded.png")
        report.add_evidence("Juego cargado", loaded)
        practice = game.is_practice_mode()
        report.check("Juego lanzado en Real Play", not practice, "Real Play",
                     "modo Práctica" if practice else "Real Play", [loaded])

        # 4. Saldo, apuesta y divisa visibles en el juego antes del giro
        idle_motion = game.measure_idle_motion(f"{ev}/frames_idle")
        hud_before = game.read_hud_stable(f"{ev}/03_hud_before")
        report.add_evidence("HUD antes del giro", hud_before["screenshot"])
        report.data["hud_before"] = hud_before
        credit_before, wager = hud_before["credit"], hud_before["bet"]

        report.check("Apuesta visible identificada", wager is not None and wager > 0, "> 0",
                     wager, [hud_before["screenshot"]], f"OCR: {hud_before['raw_text']}")
        report.check("Divisa del juego coincide con el mercado", hud_before["currency"] == currency,
                     currency, hud_before["currency"], [hud_before["screenshot"]])
        report.check("Divisa del saldo Betsson coincide con el mercado", betsson_before["currency"] == currency,
                     currency, f"{betsson_before['currency']} ('{betsson_before['raw_text']}')",
                     [f"{ev}/01_betsson_balance_before.png"])

        # 5. Localizar el control y lanzar el giro
        before_spin = game.take_game_screenshot(f"{ev}/04_before_spin.png")
        click = game.click_spin(before_spin)
        report.data["spin_click"] = click

        # 6. Verificar en pantalla que el giro empezó y terminó
        spin = game.observe_spin(before_spin, f"{ev}/frames_spin", idle_motion=idle_motion)
        report.data["spin"] = {k: v for k, v in spin.items() if k != "frames"}
        if spin["first_moving_frame"]:
            report.add_evidence("Rodillos en movimiento", spin["first_moving_frame"])
        report.check("El giro empezó (rodillos en movimiento)", spin["started"],
                     f"cambio ≥ {spin['start_threshold']:.1%} de píxeles",
                     f"máx {max(spin['ratios_vs_before'] or [0]):.1%}",
                     [before_spin, spin["first_moving_frame"]], f"Spin pulsado por {click['method']}")
        report.check("El giro terminó (rodillos detenidos)", spin["completed"],
                     f"3 fotogramas seguidos con cambio ≤ {spin['stable_threshold']:.1%}",
                     f"{'detenido' if spin['completed'] else 'no se detuvo'} en {spin['duration_sec']}s",
                     [spin["last_frame"]])

        # 7. Resultado y saldos tras el giro
        page.wait_for_timeout(1500)
        hud_after = game.read_hud_stable(f"{ev}/05_hud_after")
        report.add_evidence("HUD después del giro", hud_after["screenshot"])
        report.data["hud_after"] = hud_after
        credit_after = hud_after["credit"]

        payout, payout_source = _determine_payout(hud_after, credit_before, credit_after, wager,
                                                  spin["frames"] + [hud_after["screenshot"]])
        report.data["payout"] = {"value": payout, "source": payout_source}

        # La apuesta mostrada es la usada: el crédito cae exactamente esa cantidad al empezar el giro
        mid = game.read_hud(spin["first_moving_frame"]) if spin["first_moving_frame"] else {"credit": None}
        if mid.get("credit") is not None and credit_before is not None and wager is not None:
            deducted = round(credit_before - mid["credit"], 2)
            report.check("La apuesta mostrada es la usada en el giro", _close(deducted, wager),
                         wager, deducted, [hud_before["screenshot"], spin["first_moving_frame"]],
                         "crédito antes − crédito durante el giro")
        else:
            deducted = None if None in (credit_before, credit_after, wager) else round(credit_before - credit_after + payout, 2)
            report.check("La apuesta mostrada es la usada en el giro", _close(deducted, wager),
                         wager, deducted, [hud_before["screenshot"], hud_after["screenshot"]],
                         "crédito antes − crédito después + premio")

        in_game_ok = None not in (credit_before, wager, credit_after) and \
            validate_spin_scenario(credit_before, wager, payout, credit_after)
        report.check("Saldo del juego consistente con el giro", in_game_ok,
                     f"{credit_before} − {wager} + {payout} = "
                     f"{round(credit_before - wager + payout, 2) if None not in (credit_before, wager) else '?'}",
                     credit_after, [hud_before["screenshot"], hud_after["screenshot"]], f"premio: {payout_source}")

        # Saldo de Betsson después: balance after = balance before − wager + payout
        expected_betsson = round(betsson_before["value"] - (wager or 0) + payout, 2)
        betsson_after = lobby.refresh_balance(betsson_before["value"], expected_value=expected_betsson,
                                              screenshot_path=f"{ev}/06_betsson_balance_after.png")
        report.add_evidence("Saldo Betsson después del giro", f"{ev}/06_betsson_balance_after.png")
        report.data["betsson_after"] = betsson_after
        betsson_ok = wager is not None and validate_spin_scenario(betsson_before["value"], wager, payout,
                                                                  betsson_after["value"])
        report.check("Saldo Betsson concilia: después = antes − apuesta + premio", betsson_ok,
                     f"{betsson_before['value']} − {wager} + {payout} = {expected_betsson}",
                     betsson_after["value"],
                     [f"{ev}/01_betsson_balance_before.png", f"{ev}/06_betsson_balance_after.png"])

    except Exception as e:
        report.error = f"{type(e).__name__}: {e}"
        if page is not None:
            try:
                page.screenshot(path=f"{ev}/error.png")
                report.add_evidence("Pantalla en el momento del error", f"{ev}/error.png")
            except Exception:
                pass
        raise

    assert report.passed, f"Checks fallidos: {report.failed_checks()}"
