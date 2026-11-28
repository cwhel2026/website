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
