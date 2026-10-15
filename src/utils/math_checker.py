from typing import Dict, Any

def validate_spin_scenario(
    initial_balance: float, 
    wager: float, 
    payout: float, 
    final_balance: float, 
    tolerance: float = 0.01
) -> bool:
    """
    Valida la ecuación contable del Escenario 1 (tirada completada con saldo)[cite: 3, 23]:
    balance_after = balance_before - wager + payout[cite: 3]
    
    Args:
        initial_balance (float): Saldo antes de la tirada[cite: 3, 23].
        wager (float): Apuesta configurada en la tirada[cite: 3, 23].
        payout (float): Premio o ganancia obtenida[cite: 3, 23].
        final_balance (float): Saldo leído tras completarse el giro[cite: 3, 23].
        tolerance (float): Margen de tolerancia por redondeo decimal (por defecto 0.01).
        
    Returns:
        bool: True si la matemática concilia, False si hay desfase[cite: 23].
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
    El saldo debe permanecer inalterado tras el intento de tirada[cite: 4].
    
    Args:
        initial_balance (float): Saldo antes del intento[cite: 4].
        final_balance (float): Saldo tras el intento fallido[cite: 4].
        tolerance (float): Margen de tolerancia.
        
    Returns:
        bool: True si los saldos son idénticos, False si hubo variación[cite: 4].
    """
    difference = abs(round(initial_balance, 2) - round(final_balance, 2))
    is_unchanged = difference <= tolerance
    
    if is_unchanged:
        print(f"[PASS] Saldo inalterado tras rechazo: Antes = {initial_balance:.2f}, Después = {final_balance:.2f}")
    else:
        print(f"[FAIL] Saldo modificado indebidamente: Antes = {initial_balance:.2f}, Después = {final_balance:.2f} (Diferencia: {difference:.2f})")
        
    return is_unchanged