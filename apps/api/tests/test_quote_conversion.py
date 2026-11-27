"""Customer-facing copy for the three quotation actions."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services.quote_conversion import (
    BOOKING_SUPPORTING,
    CUSTOMER_HEADING,
    confirmation_steps,
    customer_next_steps,
    validate_conversion_request,
)


def _enquiry(**kwargs):
    defaults = {
        "intention": "estimate_requested",
        "email_delivery": "not_sent_smtp_unconfigured",
        "callback_preferred_time": None,
        "callback_phone": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_booking_copy_is_a_request_not_a_confirmed_visit():
    text = customer_next_steps(_enquiry(intention="ready_to_book"), [], email="ada@example.co.uk")
    assert text == BOOKING_SUPPORTING
    assert CUSTOMER_HEADING.startswith("Thank you")
    steps = confirmation_steps(_enquiry(intention="ready_to_book"))
    assert len(steps) == 3
    assert any("booked until we confirm" in item for item in steps)


def test_estimate_copy_does_not_claim_an_email_when_smtp_is_off():
    text = customer_next_steps(_enquiry(), [], email="ada@example.co.uk")
    assert "We have emailed" not in text
    assert "email sending is not connected" in text


def test_sent_estimate_copy_says_the_email_went():
    text = customer_next_steps(_enquiry(email_delivery="sent"), [], email="ada@example.co.uk")
    assert "We have emailed it to ada@example.co.uk" in text


def test_callback_copy_names_the_requested_time():
    text = customer_next_steps(
        _enquiry(intention="callback_requested", callback_preferred_time="Weekday mornings"),
        [],
        email="ada@example.co.uk",
    )
    assert "Weekday mornings" in text


def test_marketing_consent_is_not_required():
    body = SimpleNamespace(
        intention="estimate_requested",
        email="ada@example.co.uk",
        full_name="Ada Customer",
        address_line1="1 Lane",
        phone=None,
        callback_preferred_time=None,
        consent_marketing=False,
    )
    validate_conversion_request(body)


def test_callback_requires_a_phone_and_a_time():
    body = SimpleNamespace(
        intention="callback_requested",
        email="ada@example.co.uk",
        full_name="Ada Customer",
        address_line1="1 Lane",
        phone="07",
        callback_preferred_time="",
        consent_marketing=False,
    )
    with pytest.raises(HTTPException):
        validate_conversion_request(body)
