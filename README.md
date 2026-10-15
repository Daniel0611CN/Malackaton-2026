# Equipo ADVM: RETO BETSSON (Malackaton 2026)

Checker que navega el casino de Betsson, lanza un juego de Pragmatic Play en **Real Play** y valida
los dos escenarios del reto **usando solo lo que el jugador ve en pantalla**.

| Qué se verifica | Cómo |
|---|---|
| Saldo de Betsson | Texto visible del header (antes y después, recargando el lobby) |
| Botón Spin / pantalla de intro | Template matching multiescala (`assets/template_spin_arrows.png`) |
| Crédito, apuesta, premio y divisa del juego | OCR (EasyOCR) del HUD del canvas, localizando las etiquetas `CRÉDITO/CREDIT`, `APUESTA/BET`, `GANANCIA/WIN` |
| El giro empezó y terminó | Diferencia entre fotogramas del canvas, calibrada con la animación en reposo |
| Aviso de saldo insuficiente e idioma | OCR de la página completa (+ texto del DOM accesible como apoyo) |
| Conciliación | `balance after = balance before − wager + payout` (juego y Betsson) |

## Estructura

```
config/                  Configuración por mercado (URL, divisa, idioma, etiquetas HUD, palabras clave)
src/config.py            Carga de config y credenciales (desde variables de entorno)
src/pages/lobby_page.py  Lobby: popups, login, saldo del header, lanzar juego Pragmatic
src/pages/game_page.py   Juego: popups DGOJ, Real Play, canvas, HUD por OCR, spin y observación del giro
src/utils/               Librerías de detección: vision_helper, ocr_helper, math_checker, report_helper
tests/                   Los dos escenarios (pytest) + fixtures (navegador, sesión, informe)
scripts/build_report.py  Genera el informe HTML a partir de los resultados
test/                    Pruebas manuales offline de las librerías con capturas reales
```

## Ejecutar en local

Linux / macOS:

```bash
pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env            # y rellena las cuentas de prueba (NUNCA se sube)

TARGET_MARKET=betsson_com HEADLESS=0 python -m pytest
python scripts/build_report.py reports        # abre reports/index.html
```

Windows (PowerShell):

```powershell
pip install -r requirements.txt
python -m playwright install chromium
Copy-Item .env.example .env     # y rellena las cuentas de prueba

.\run_local.ps1 -Market betsson_com
```

(Si PowerShell bloquea el script: `Set-ExecutionPolicy -Scope Process Bypass`.)

Solo un escenario: `python -m pytest tests/test_scenario2_insufficient_balance.py`.

## GitHub Actions

`.github/workflows/test-runner.yml` ejecuta ambos escenarios **una vez por mercado** (matriz
`betsson_com`) y publica:

- `informe-betsson_com`: informe HTML, JSON por escenario, capturas, vídeo y trace de Playwright.
- `informe-completo`: los dos mercados juntos con un `index.html` común.
- Tabla PASS/FAIL por check en el resumen del run.

Secrets necesarios (Settings → Secrets and variables → Actions):
`BETSSON_COM_USER`, `BETSSON_COM_PASS`, `BETSSON_COM_NOFUND_USER`, `BETSSON_COM_NOFUND_PASS`.

## Sin secretos en las evidencias

El login se hace en un contexto de navegador **sin grabar**; la sesión se transfiere a otro contexto
que graba vídeo y trace. Las credenciales solo se leen de variables de entorno.


## Nota del equipo

Las pruebas de Actions de Github fallan debido a una no respuesta de los servidores en los que corren
las máquinas de Github (EEUU), el timeout del script cancela la espera y por eso no genera un reporte satisfactorio.
En local, con los pasos detallados arriba, sí funciona y genera unos reportes satisfactorios acordes a lo requerido.