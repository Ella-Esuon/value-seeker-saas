from typing import List, Dict


def calculate_monthly_installment(principal: float, annual_rate: float, term_months: int) -> float:
    if annual_rate == 0:
        return round(principal / term_months, 2)
    r = annual_rate / 100 / 12
    installment = principal * r * (1 + r) ** term_months / ((1 + r) ** term_months - 1)
    return round(installment, 2)


def amortization_schedule(principal: float, annual_rate: float, term_months: int) -> List[Dict]:
    installment = calculate_monthly_installment(principal, annual_rate, term_months)
    r = annual_rate / 100 / 12
    balance = principal
    schedule = []
    for i in range(1, term_months + 1):
        interest = round(balance * r, 2)
        principal_paid = round(min(installment - interest, balance), 2)
        balance = round(max(0.0, balance - principal_paid), 2)
        actual_payment = round(principal_paid + interest, 2)
        schedule.append({
            "payment_number": i,
            "monthly_installment": actual_payment,
            "principal": principal_paid,
            "interest": interest,
            "balance": balance,
        })
    return schedule


def split_repayment(current_balance: float, annual_rate: float, amount: float):
    r = annual_rate / 100 / 12
    interest = round(current_balance * r, 2)
    principal = round(min(amount - interest, current_balance), 2)
    if principal < 0:
        principal = 0.0
        interest = round(min(amount, current_balance * r), 2)
    new_balance = round(max(0.0, current_balance - principal), 2)
    return principal, interest, new_balance
