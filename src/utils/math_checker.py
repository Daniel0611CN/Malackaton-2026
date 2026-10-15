def validate_spin_scenario(initial_balance: float, wager: float, payout: float, final_balance: float) -> bool:
    """
    Validates the fundamental casino equation to ensure financial integrity.
    Formula: Final Balance = Initial Balance - Wager + Payout.
    
    Args:
        initial_balance (float): The player balance read before the spin.
        wager (float): The amount bet on the spin.
        payout (float): The amount won from the spin.
        final_balance (float): The player balance read after the spin completes.
        
    Returns:
        bool: True if the math reconciles perfectly according to business rules, False otherwise.
    """
    is_valid = False
    
    # Calculate the expected balance[cite: 2]
    # round() is used to prevent standard floating-point arithmetic errors in Python
    expected_balance = round((initial_balance - wager + payout), 2)
    actual_final_balance = round(final_balance, 2)
    
    # Check if the casino logic is mathematically correct
    if actual_final_balance == expected_balance:
        print(f"SUCCESS - Math reconciles: {initial_balance} - {wager} + {payout} = {actual_final_balance}")
        is_valid = True
    else:
        print(f"FAILURE - Math mismatch: Expected {expected_balance}, but got {actual_final_balance}")
        
    return is_valid