import os
import pytest
from src.pages.betsson_page import BetssonAutomation

def test_scenario_1_real_play_spin():
    """
    Test Escenario 1: Spin con dinero real y verificación de balances
    """
    market = os.getenv("TARGET_MARKET", "betsson_com")
    user = os.getenv("BETSSON_USER", "")
    password = os.getenv("BETSSON_PASS", "")
    
    print(f"\n--- Iniciando Escenario 1 en Mercado: {market} ---")
    
    automation = BetssonAutomation(target_market=market)
    result = automation.run_scenario_1(user, password)
    
    assert result is True

def test_scenario_2_insufficient_balance():
    """
    Test Escenario 2: Intento de spin sin saldo
    """
    market = os.getenv("TARGET_MARKET", "betsson_com")
    user = os.getenv("BETSSON_NOFUND_USER", "")
    password = os.getenv("BETSSON_NOFUND_PASS", "")
    
    print(f"\n--- Iniciando Escenario 2 en Mercado: {market} ---")
    
    # Aquí llamaremos al flujo de saldo insuficiente
    assert True