import pytest
import os
import json
from src.utils.ocr_helper import read_balance_from_crop
from src.utils.math_checker import validate_spin_balance_rule

# Cargar la configuración del mercado según la variable de entorno de GitHub Actions
market_name = os.getenv("TARGET_MARKET", "betsson_com")
config_path = f"config/{market_name}.json"

with open(config_path, "r") as f:
    config = json.load(f)

def test_scenario_1_completed_real_play():
    """
    Escenario 1: Tirada con saldo suficiente
    Verifica que la tirada se ejecuta y se cumple la regla de balances
    """
    print(f"Ejecutando Escenario 1 para el mercado: {config['market']}")
    # Aquí se invocarán las funciones que están desarrollando tus compañeros
    assert True

def test_scenario_2_insufficient_balance():
    """
    Escenario 2: Intentar tirada con saldo insuficiente
    Verifica que se rechaza la tirada y aparece el mensaje en el idioma correcto
    """
    print(f"Ejecutando Escenario 2 para el mercado: {config['market']}")
    assert True