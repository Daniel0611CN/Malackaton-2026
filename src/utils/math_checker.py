from typing import Dict, Any

def validate_spin_scenario(
    initial_balance: float, 
    wager: float, 
    payout: float, 
    final_balance: float, 
    tolerance: float = 0.01
) -> bool:
    """
    Valida la ecuación contable del Escenario 1 (tirada completada con saldo):
    balance_after = balance_before - wager + payout
    
    Args:
        initial_balance (float): Saldo antes de la tirada.
        wager (float): Apuesta configurada en la tirada.
        payout (float): Premio o ganancia obtenida.
        final_balance (float): Saldo leído tras completarse el giro.
        tolerance (float): Margen de tolerancia por redondeo decimal (por defecto 0.01).
        
    Returns:
        bool: True si la matemática concilia, False si hay desfase.
    """
    expected_balance = round(initial_balance - wager + payout, 2)
    actual_balance = round(final_balance, 2)
    discrepancy = abs(expected_balance - actual_balance)
    
    is_valid = discrepancy <= tolerance
    
    if is_valid:
        print(f"[PASS] Conciliación contable OK: {initial_balance:.2f} - {wager:.2f} + {payout:.2f} = {actual_balance:.2f}")
    else:
        print(f"[FAIL] Desfase contable: Esperado {expected_balance:.2f}, pero se obtuvo {actual_balance:.2f} (Diferencia: {discrepancy:.2f})")
        
    return is_valid


def validate_insufficient_balance_scenario(
    initial_balance: float, 
    final_balance: float, 
    tolerance: float = 0.01
) -> bool:
    """
    Valida la regla del Escenario 2 (Saldo insuficiente):
    El saldo debe permanecer inalterado tras el intento de tirada.
    
    Args:
        initial_balance (float): Saldo antes del intento.
        final_balance (float): Saldo tras el intento fallido.
        tolerance (float): Margen de tolerancia.
        
    Returns:
        bool: True si los saldos son idénticos, False si hubo variación.
    """
    difference = abs(round(initial_balance, 2) - round(final_balance, 2))
    is_unchanged = difference <= tolerance
    
    if is_unchanged:
        print(f"[PASS] Saldo inalterado tras rechazo: Antes = {initial_balance:.2f}, Después = {final_balance:.2f}")
    else:
        print(f"[FAIL] Saldo modificado indebidamente: Antes = {initial_balance:.2f}, Después = {final_balance:.2f} (Diferencia: {difference:.2f})")
        
    return is_unchanged