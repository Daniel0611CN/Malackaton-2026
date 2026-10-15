import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

# Carpeta estándar de capturas en la raíz del proyecto
SCREENSHOTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "screenshots")
)

def save_evidence_screenshot(page_or_image_path, screenshot_name: str) -> str:
    """
    Guarda o copia una captura de pantalla en la carpeta screenshots/
    para que GitHub Actions la archive como evidencia del test.
    
    Acepta tanto el objeto 'page' de Playwright como una ruta de archivo local.
    """
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    destination_path = os.path.join(SCREENSHOTS_DIR, f"{screenshot_name}.png")

    # Si es el objeto page de Playwright
    if hasattr(page_or_image_path, "screenshot"):
        page_or_image_path.screenshot(path=destination_path)
    # Si es una ruta de imagen local que queremos archivar como evidencia
    elif isinstance(page_or_image_path, str) and os.path.exists(page_or_image_path):
        import shutil
        shutil.copy(page_or_image_path, destination_path)
    else:
        print(f"[REPORT ERROR] No se pudo guardar la evidencia para '{screenshot_name}'.")
        return ""

    print(f"[EVIDENCIA GUARDADA]: {destination_path}")
    return destination_path


def log_test_verdict(
    market: str, 
    scenario: str, 
    passed: bool, 
    details: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Registra el veredicto estructurado para el reporte del entregable.
    
    Args:
        market: 'betsson.com'
        scenario: 'Scenario 1 (Real Play)' o 'Scenario 2 (Insufficient balance)'
        passed: True si todas las verificaciones cumplieron, False si hubo fallo
        details: Diccionario con saldos leídos, wager, payout y evidencia asociada
    """
    verdict_entry = {
        "timestamp": datetime.now().isoformat(),
        "market": market,
        "scenario": scenario,
        "status": "PASS" if passed else "FAIL",
        "checks": details
    }

    # Guarda / anexa un resumen JSON de la ejecución
    summary_file = os.path.join(SCREENSHOTS_DIR, "validation_summary.json")
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    history = []
    if os.path.exists(summary_file):
        try:
            with open(summary_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    history.append(verdict_entry)
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

    print(f"\n[VEREDICTO REGISTRADO] {scenario} en {market}: {verdict_entry['status']}")
    return verdict_entry

# ---------------------------------------------------------------------------
# Informe por check (escenario x mercado) para el entregable "Report and evidence"
# ---------------------------------------------------------------------------

REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "reports"))


class ScenarioReport:
    """
    Acumula los checks de un escenario en un mercado. Cada check guarda lo esperado,
    lo observado en pantalla y las capturas que lo demuestran.
    """

    def __init__(self, market: str, market_label: str, scenario_id: str, scenario_name: str, output_dir: str):
        self.market = market
        self.market_label = market_label
        self.scenario_id = scenario_id
        self.scenario_name = scenario_name
        self.output_dir = output_dir
        self.started_at = datetime.now().isoformat(timespec="seconds")
        self.checks = []
        self.evidence = []
        self.data = {}
        self.error = None

    def check(self, name: str, passed: bool, expected: Any = None, observed: Any = None,
              evidence: Optional[List[str]] = None, note: str = "") -> bool:
        passed = bool(passed)
        self.checks.append({
            "name": name,
            "status": "PASS" if passed else "FAIL",
            "expected": expected,
            "observed": observed,
            "note": note,
            "evidence": [self._rel(p) for p in (evidence or []) if p],
        })
        print(f"[CHECK] {'PASS' if passed else 'FAIL'} - {name} | esperado={expected} observado={observed} {note}")
        return passed

    def add_evidence(self, label: str, path: Optional[str]):
        if path and os.path.exists(path):
            self.evidence.append({"label": label, "path": self._rel(path)})

    def _rel(self, path: str) -> str:
        return os.path.relpath(os.path.abspath(path), self.output_dir).replace(os.sep, "/")

    @property
    def passed(self) -> bool:
        return self.error is None and bool(self.checks) and all(c["status"] == "PASS" for c in self.checks)

    def failed_checks(self) -> List[str]:
        return [c["name"] for c in self.checks if c["status"] == "FAIL"]

    def save(self) -> str:
        os.makedirs(self.output_dir, exist_ok=True)
        path = os.path.join(self.output_dir, f"{self.scenario_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "market": self.market,
                "market_label": self.market_label,
                "scenario_id": self.scenario_id,
                "scenario": self.scenario_name,
                "status": "PASS" if self.passed else "FAIL",
                "started_at": self.started_at,
                "finished_at": datetime.now().isoformat(timespec="seconds"),
                "error": self.error,
                "checks": self.checks,
                "evidence": self.evidence,
                "data": self.data,
            }, f, indent=2, ensure_ascii=False, default=str)
        return path


def _esc(value: Any) -> str:
    import html
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return html.escape(str(value))


_REPORT_CSS = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#f6f7f9;color:#1d2330}
header{background:#ff6600;color:#fff;padding:20px 32px}header h1{margin:0;font-size:22px}
header p{margin:4px 0 0;opacity:.9}main{padding:24px 32px;max-width:1200px}
.summary{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:24px}
.tile{background:#fff;border-radius:8px;padding:12px 16px;box-shadow:0 1px 3px #0002;min-width:220px}
.tile b{display:block;font-size:13px;color:#566}
section{background:#fff;border-radius:8px;box-shadow:0 1px 3px #0002;margin-bottom:24px;padding:16px 20px}
h2{margin:0 0 8px;font-size:18px}table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid #e3e6ea;vertical-align:top}
th{background:#f0f2f5}.PASS{color:#0a7a3d;font-weight:700}.FAIL{color:#c0262d;font-weight:700}
.badge{display:inline-block;padding:2px 10px;border-radius:12px;color:#fff;font-size:13px;font-weight:700}
.badge.PASS{background:#0a7a3d;color:#fff}.badge.FAIL{background:#c0262d;color:#fff}
.gallery{display:flex;flex-wrap:wrap;gap:12px;margin-top:12px}
.gallery figure{margin:0;width:280px}.gallery img{width:100%;border:1px solid #ccd;border-radius:4px}
figcaption{font-size:12px;color:#566}.err{background:#fde8e8;padding:8px;border-radius:4px;white-space:pre-wrap;font-size:13px}
td a{font-size:12px}
"""


def build_html_report(results_dir: str, output_path: Optional[str] = None, title: str = None) -> str:
    """
    Genera un informe HTML (sin dependencias) a partir de todos los <escenario>.json que haya
    bajo results_dir (recursivo). Las imágenes se enlazan con rutas relativas, así el ZIP del
    artefacto de GitHub Actions se abre directamente en el navegador.
    """
    output_path = output_path or os.path.join(results_dir, "index.html")
    out_dir = os.path.dirname(os.path.abspath(output_path))
    results = []
    for root, _, files in os.walk(results_dir):
        for name in sorted(files):
            if name.startswith("scenario") and name.endswith(".json"):
                with open(os.path.join(root, name), encoding="utf-8") as f:
                    res = json.load(f)
                res["_base"] = os.path.relpath(root, out_dir).replace(os.sep, "/")
                results.append(res)
    results.sort(key=lambda r: (r["market"], r["scenario_id"]))

    def link(base: str, rel: str) -> str:
        return rel if base in ("", ".") else f"{base}/{rel}"

    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    parts = [
        "<!doctype html><html lang='es'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        f"<title>{_esc(title or 'Informe de validación')}</title><style>{_REPORT_CSS}</style></head><body>",
        f"<header><h1>{_esc(title or 'Betsson · Intelligent Game Validation')}</h1>",
        f"<p>Generado {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · {passed}/{total} escenarios PASS</p></header><main>",
        "<div class='summary'>",
    ]
    for r in results:
        parts.append(f"<div class='tile'><b>{_esc(r['market_label'])}</b>{_esc(r['scenario'])}<br>"
                     f"<span class='badge {r['status']}'>{r['status']}</span></div>")
    parts.append("</div>")
    if not results:
        parts.append("<section><p>No se encontraron resultados de escenarios.</p></section>")

    for r in results:
        base = r["_base"]
        parts.append(f"<section><h2>{_esc(r['scenario'])} · {_esc(r['market_label'])} "
                     f"<span class='badge {r['status']}'>{r['status']}</span></h2>")
        parts.append(f"<p>Inicio {_esc(r['started_at'])} · fin {_esc(r['finished_at'])}</p>")
        if r.get("error"):
            parts.append(f"<div class='err'><b>Error de ejecución:</b> {_esc(r['error'])}</div>")
        parts.append("<table><tr><th>Check</th><th>Resultado</th><th>Esperado</th><th>Observado en pantalla</th><th>Evidencia</th></tr>")
        for c in r["checks"]:
            ev = " ".join(f"<a href='{_esc(link(base, p))}'>{_esc(os.path.basename(p))}</a>" for p in c["evidence"])
            note = f"<br><small>{_esc(c['note'])}</small>" if c.get("note") else ""
            parts.append(f"<tr><td>{_esc(c['name'])}{note}</td><td class='{c['status']}'>{c['status']}</td>"
                         f"<td>{_esc(c['expected'])}</td><td>{_esc(c['observed'])}</td><td>{ev}</td></tr>")
        parts.append("</table><div class='gallery'>")
        for e in r["evidence"]:
            src = _esc(link(base, e["path"]))
            if e["path"].lower().endswith((".png", ".jpg", ".jpeg")):
                parts.append(f"<figure><a href='{src}'><img src='{src}' loading='lazy'></a>"
                             f"<figcaption>{_esc(e['label'])}</figcaption></figure>")
            else:
                parts.append(f"<figure><a href='{src}'>{_esc(e['label'])}</a></figure>")
        parts.append("</div></section>")

    parts.append("</main></body></html>")
    os.makedirs(out_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    return output_path


def build_markdown_summary(results_dir: str) -> str:
    """Tabla Markdown para $GITHUB_STEP_SUMMARY."""
    rows = ["| Mercado | Escenario | Check | Resultado | Esperado | Observado |", "|---|---|---|---|---|---|"]
    for root, _, files in os.walk(results_dir):
        for name in sorted(files):
            if name.startswith("scenario") and name.endswith(".json"):
                with open(os.path.join(root, name), encoding="utf-8") as f:
                    r = json.load(f)
                if r.get("error"):
                    rows.append(f"| {r['market_label']} | {r['scenario']} | Ejecución | ❌ FAIL | — | {str(r['error'])[:120]} |")
                for c in r["checks"]:
                    icon = "✅" if c["status"] == "PASS" else "❌"
                    rows.append(f"| {r['market_label']} | {r['scenario']} | {c['name']} | {icon} {c['status']} "
                                f"| {c['expected']} | {c['observed']} |")
    return "\n".join(rows)
