"""
Escenario 2 — Insufficient balance.

Con la cuenta sin saldo se intenta un giro y se verifica, con lo que ve el jugador, que el
giro se rechaza, que aparece el aviso en el idioma del mercado y que ningún saldo cambia.
"""
from src.pages.game_page import GamePage
from src.utils.math_checker import validate_insufficient_balance_scenario
from src.utils.ocr_helper import find_keywords


def _snippet(text: str, keywords, width: int = 90) -> str:
    lowered = text.lower()
    for kw in keywords:
        idx = lowered.find(kw.lower())
        if idx >= 0:
            return "…" + text[max(0, idx - width // 2): idx + width // 2].strip() + "…"
    return text[:width]


def test_scenario_2_insufficient_balance(market_config, open_session, scenario_report):
    cfg = market_config
    currency = cfg["currency"]
    report = scenario_report("scenario2_insufficient_balance", "Escenario 2 · Saldo insuficiente")
    ev = report.evidence_dir
    page = None

    try:
        page, lobby = open_session("no_funds", ev)

        betsson_before = lobby.get_betsson_balance(screenshot_path=f"{ev}/01_betsson_balance_before.png")
        report.add_evidence("Saldo Betsson antes del intento", f"{ev}/01_betsson_balance_before.png")
        report.data["betsson_before"] = betsson_before

        lobby.open_pragmatic_game()
        game = GamePage(page, cfg, ev)
        game.wait_for_game_ready()
        loaded = game.take_page_screenshot(f"{ev}/02_game_loaded.png")
        report.add_evidence("Juego cargado", loaded)
        practice = game.is_practice_mode()
        report.check("Juego lanzado en Real Play", not practice, "Real Play",
                     "modo Práctica" if practice else "Real Play", [loaded])

        # Saldo antes del intento
        idle_motion = game.measure_idle_motion(f"{ev}/frames_idle")
        hud_before = game.read_hud_stable(f"{ev}/03_hud_before")
        report.add_evidence("HUD antes del intento", hud_before["screenshot"])
        report.data["hud_before"] = hud_before

        observed_currency = hud_before["currency"] or betsson_before["currency"]
        report.check("Divisa mostrada coincide con el mercado", observed_currency == currency, currency,
                     f"juego={hud_before['currency']} · Betsson={betsson_before['currency']}",
                     [hud_before["screenshot"], f"{ev}/01_betsson_balance_before.png"])

        # Intento de giro
        before_spin = game.take_game_screenshot(f"{ev}/04_before_spin.png")
        click = game.click_spin(before_spin)
        report.data["spin_click"] = click
        spin = game.observe_spin(before_spin, f"{ev}/frames_spin", idle_motion=idle_motion, timeout_sec=12)
        report.data["spin"] = {k: v for k, v in spin.items() if k != "frames"}

        # Aviso de saldo insuficiente, tal y como lo ve el jugador (en cualquier idioma)
        by_language = cfg["insufficient_keywords_by_language"]
        expected_keywords = by_language[cfg["language"]]
        other_keywords = [kw for lang, kws in by_language.items() if lang != cfg["language"] for kw in kws]
        message = game.wait_for_insufficient_funds_message(expected_keywords + other_keywords,
                                                           f"{ev}/05_after_spin_attempt")
        report.add_evidence("Pantalla tras el intento de giro", message["screenshot"])
        report.data["message"] = {k: v for k, v in message.items() if k != "text"}

        expected_lang_hits = find_keywords(message["text"], expected_keywords)
        other_lang_hits = find_keywords(message["text"], other_keywords)
        report.check("Aviso de saldo insuficiente visible", message["detected"],
                     "mensaje visible tras pulsar Spin",
                     _snippet(message["text"], message.get("keywords") or []) if message["detected"] else "sin aviso",
                     [message["screenshot"]], f"detectado por {message['source'] or '—'}")
        report.check(f"Aviso en el idioma del mercado ({cfg['language']})",
                     bool(expected_lang_hits) and not other_lang_hits,
                     f"palabras clave {cfg['language']}: {', '.join(expected_keywords[:3])}…",
                     f"{cfg['language']}={expected_lang_hits} · otro idioma={other_lang_hits}",
                     [message["screenshot"]])

        # Saldos después del intento
        hud_after = game.read_hud_stable(f"{ev}/06_hud_after")
        report.add_evidence("HUD después del intento", hud_after["screenshot"])
        report.data["hud_after"] = hud_after
        credit_before, credit_after = hud_before["credit"], hud_after["credit"]
        in_game_unchanged = None not in (credit_before, credit_after) and \
            validate_insufficient_balance_scenario(credit_before, credit_after)

        completed_paid_spin = spin["completed"] and credit_before is not None and credit_after is not None \
            and credit_after < credit_before
        report.check("El giro se rechaza (no se completa un giro pagado)",
                     message["detected"] and not completed_paid_spin and in_game_unchanged,
                     "aviso visible y crédito sin descontar",
                     f"aviso={message['detected']} · crédito {credit_before} → {credit_after}",
                     [before_spin, message["screenshot"]])
        report.check("Saldo del juego no cambia", in_game_unchanged, credit_before, credit_after,
                     [hud_before["screenshot"], hud_after["screenshot"]])

        page.wait_for_timeout(3000)
        betsson_after = lobby.refresh_balance(betsson_before["value"], expected_value=betsson_before["value"],
                                              screenshot_path=f"{ev}/07_betsson_balance_after.png")
        report.add_evidence("Saldo Betsson después del intento", f"{ev}/07_betsson_balance_after.png")
        report.data["betsson_after"] = betsson_after
        report.check("Saldo Betsson no cambia",
                     validate_insufficient_balance_scenario(betsson_before["value"], betsson_after["value"]),
                     betsson_before["value"], betsson_after["value"],
                     [f"{ev}/01_betsson_balance_before.png", f"{ev}/07_betsson_balance_after.png"])

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
