"""
Core financial logic for WACC calculations.
Reusable module imported by app.py.
"""

def cost_of_equity_dgm(D0, g, P0):
    """
    Cost of Equity using Gordon Growth Model (Dividend Growth Model):
        R_e = (D1 / P0) + g
    """
    D1 = D0 * (1 + g)
    return (D1 / P0) + g


def cost_of_preference_shares(Dp, P0):
    """
    Cost of irredeemable preference shares:
        R_p = D_p / P0
    """
    return Dp / P0


def cost_of_redeemable_debt(I, P0, RV, n, tax_rate):
    """
    After-tax cost of redeemable debt using the yield-to-redemption approximation:
        R_d(1-T) = ((I + (RV - P0)/n) / ((RV + P0)/2)) * (1 - T)
    """
    pre_tax = (I + (RV - P0) / n) / ((RV + P0) / 2)
    return pre_tax * (1 - tax_rate)


def cost_of_irredeemable_debt(I, P0, tax_rate):
    """
    After-tax cost of irredeemable debt:
        R_d(1-T) = (I / P0) * (1 - T)
    """
    return (I / P0) * (1 - tax_rate)


def cost_of_bank_loans(interest_rate, tax_rate):
    """
    After-tax cost of bank borrowing:
        R_d(1-T) = i(1 - T)
    """
    return interest_rate * (1 - tax_rate)


def calculate_weights(values):
    """
    Convert a list of financing values into fractional weights.
    """
    total = sum(values)
    if total == 0:
        return [0 for _ in values]
    return [v / total for v in values]


def calculate_wacc(costs, weights):
    """
    Weighted Average Cost of Capital:
        Σ (cost_i * weight_i)
    """
    return sum(c * w for c, w in zip(costs, weights))
