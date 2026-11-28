from decimal import Decimal, InvalidOperation

def validate_allocation(weekly_limit, already_spent, allocations):
    try:
        limit, spent = (Decimal(str(v)) for v in (weekly_limit, already_spent))
        if not isinstance(allocations, list) or not 1 <= len(allocations) <= 20:
            raise ValueError()
        rows = []
        for row in allocations:
            name = row["territory"]
            daily = Decimal(str(row["daily_gbp"]))
            days = row["days"]
            if not isinstance(name, str) or not name.strip() or type(days) is not int or not 1 <= days <= 7:
                raise ValueError()
            if not daily.is_finite() or daily < 0 or daily != daily.quantize(Decimal("0.01")):
                raise ValueError()
            rows.append({"territory": name, "daily_gbp": str(daily), "days": days, "total_gbp": str(daily * days)})
        if not all(v.is_finite() and v >= 0 for v in (limit, spent)):
            raise ValueError()
        total = sum((Decimal(row["total_gbp"]) for row in rows), Decimal(0))
        remaining = max(Decimal(0), limit - spent)
        return {"valid": total <= remaining, "total_gbp": str(total), "remaining_gbp": str(remaining), "overspend_gbp": str(max(Decimal(0), total - remaining)), "allocations": rows, "basis": "Arithmetic only; not spending approval or verified platform availability."}
    except (ValueError, TypeError, KeyError, InvalidOperation, ArithmeticError):
        return {"valid": False, "error": "Invalid budget inputs"}


def campaign_budget(policy, spend, requested, commitments=0):
    """One conservative planning ceiling. Provisional records never authorise spend.

Legacy spend rows are cumulative campaign counters, not dated transactions. Until
period billing exists, count the entire supplied amount against both periods.
    """
    from decimal import ROUND_DOWN
    try:
        def value(x):
            n = Decimal(str(x))
            if not n.is_finite() or n < 0:
                raise ValueError()
            return n
        requested = value(requested)
        weekly = value(policy['weekly_limit_gbp'])
        monthly = value(policy['monthly_limit_gbp'])
        daily = value(policy['daily_limit_gbp'])
        platform_daily = value(policy.get('meta_daily_limit_gbp', daily))
        platform_weekly = value(policy.get('meta_weekly_budget_gbp', weekly))
        spent = value(spend['total_spent_gbp'])
        monthly_spent = value(spend.get('monthly_spent_gbp', spent))
        committed_daily = value(commitments)
        buffer = value(policy.get('meta_safety_buffer_pct', 0))
        if buffer >= 100:
            raise ValueError()
        ceiling = max(Decimal(0), min(requested, weekly-spent-committed_daily*7, platform_weekly-spent-committed_daily*7, monthly-monthly_spent-committed_daily*31, (daily-committed_daily)*7, (platform_daily-committed_daily)*7))
        usable = ceiling * (1-buffer/100)
        per_day = (usable/7).quantize(Decimal('.01'), rounding=ROUND_DOWN)
        return {'daily_gbp': str(per_day), 'total_gbp': str(per_day*7), 'requested_gbp': str(requested), 'safety_buffer_pct': str(buffer), 'reserved_buffer_gbp': str(ceiling-per_day*7), 'authorised_spend_gbp': '0', 'basis': 'Conservative planning ceiling; cumulative recorded spend is not verified period billing'}
    except (KeyError, TypeError, ValueError, InvalidOperation, ArithmeticError):
        return {'error': 'Budget evidence unavailable or invalid', 'authorised_spend_gbp': '0'}
