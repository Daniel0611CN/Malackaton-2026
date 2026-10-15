import os
import shutil
import sys
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_market_config, get_credentials  # noqa: E402
from src.pages.lobby_page import LobbyPage  # noqa: E402
from src.utils.report_helper import ScenarioReport, REPORTS_DIR  # noqa: E402

VIEWPORT = {"width": 1920, "height": 1080}
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
LAUNCH_ARGS = [
    # Flags para evitar detección de bots y bloqueos WAF
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    # WebGL por software: sin esto el canvas del juego sale negro en CI/headless
    "--use-angle=swiftshader",
    "--enable-unsafe-swiftshader",
    "--ignore-gpu-blocklist",
]


def _env_flag(name: str, default: str = "1") -> bool:
    return os.getenv(name, default).strip().lower() not in ("0", "false", "no", "")


@pytest.fixture(scope="session")
def market_config():
    return load_market_config()


@pytest.fixture(scope="session")
def market_dir(market_config):
    path = os.path.join(REPORTS_DIR, market_config["market"])
    os.makedirs(path, exist_ok=True)
    return path


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=_env_flag("HEADLESS", "1"), args=LAUNCH_ARGS,
                                    executable_path=os.getenv("CHROMIUM_PATH") or None)
        yield browser
        browser.close()


def _new_context(browser, **kwargs):
    context = browser.new_context(viewport=VIEWPORT, user_agent=USER_AGENT, device_scale_factor=1,
                                  locale=kwargs.pop("locale", None), **kwargs)
    context.add_init_script("delete Object.getPrototypeOf(navigator).webdriver")
    return context


@pytest.fixture
def open_session(browser, market_config, scenario_report):
    # Depende de scenario_report para que el informe se guarde DESPUÉS de cerrar el contexto
    # (el vídeo y el trace solo existen en disco tras el cierre).
    """
    Devuelve una función open_session(account, evidence_dir) -> (page, lobby) ya logueada.

    El login se hace en un contexto SIN grabación; la sesión se pasa (storage_state) a un
    segundo contexto que graba vídeo y trace. Así las evidencias no contienen credenciales.
    """
    opened = []
    locale = market_config.get("locale", "en-GB")

    def _open(account: str, evidence_dir: str):
        user, password = get_credentials(market_config, account)

        login_ctx = _new_context(browser, locale=locale)
        login_page = login_ctx.new_page()
        login_lobby = LobbyPage(login_page, market_config, evidence_dir)
        login_lobby.navigate()
        login_lobby.login(user, password)
        state = login_ctx.storage_state()
        login_ctx.close()

        video_dir = os.path.join(evidence_dir, "video")
        record = {"record_video_dir": video_dir, "record_video_size": VIEWPORT} if _env_flag("RECORD_VIDEO") else {}
        ctx = _new_context(browser, locale=locale, storage_state=state, **record)
        page = ctx.new_page()
        lobby = LobbyPage(page, market_config, evidence_dir)
        lobby.navigate()
        if not lobby.is_logged_in():
            # La sesión no sobrevivió al cambio de contexto: login de nuevo (antes de iniciar el trace)
            print("[SESIÓN] storage_state insuficiente, repitiendo login en el contexto grabado.")
            lobby.login(user, password)
        ctx.tracing.start(screenshots=True, snapshots=True)
        opened.append((ctx, page, evidence_dir))
        return page, lobby

    yield _open

    for ctx, page, evidence_dir in opened:
        try:
            ctx.tracing.stop(path=os.path.join(evidence_dir, "trace.zip"))
        except Exception as e:
            print(f"[TRACE] No se pudo guardar el trace: {e}")
        video = page.video
        ctx.close()
        if video:
            try:
                shutil.move(video.path(), os.path.join(evidence_dir, "video.webm"))
                shutil.rmtree(os.path.join(evidence_dir, "video"), ignore_errors=True)
            except Exception as e:
                print(f"[VIDEO] No se pudo mover el vídeo: {e}")


@pytest.fixture
def scenario_report(market_config, market_dir):
    """Crea el ScenarioReport del test y lo guarda siempre (pase, falle o explote)."""
    reports = []

    def _make(scenario_id: str, scenario_name: str) -> ScenarioReport:
        output_dir = os.path.join(market_dir, scenario_id)
        shutil.rmtree(output_dir, ignore_errors=True)
        os.makedirs(output_dir, exist_ok=True)
        report = ScenarioReport(market_config["market"], market_config.get("label", market_config["market"]),
                                scenario_id, scenario_name, market_dir)
        report.evidence_dir = output_dir
        reports.append(report)
        return report

    yield _make

    for report in reports:
        for name, label in (("video.webm", "Vídeo de la ejecución"), ("trace.zip", "Playwright trace")):
            report.add_evidence(label, os.path.join(report.evidence_dir, name))
        print(f"[INFORME] {report.save()}")
