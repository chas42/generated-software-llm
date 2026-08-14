"""
Flask app implementing a simple Credit Card <-> Phone association storage.

OpenAPI endpoints:
- POST /associate_card
- POST /retrieve_cards

This service keeps data in memory for simplicity.

Security note:
Real credit card numbers are sensitive. This sample is for controlled/test
environments only.
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from flask import Flask, jsonify, request

app = Flask(__name__)

# -----------------------------
# In-memory storage
# -----------------------------


@dataclass
class Storage:
    phone_to_cards: Dict[str, Set[str]]
    lock: threading.RLock


STORE = Storage(phone_to_cards={}, lock=threading.RLock())

# -----------------------------
# Helpers
# -----------------------------

_PHONE_RE = re.compile(r"^[0-9+()\-\s]{3,40}$")


def _json_error(message: str, status_code: int):
    resp = jsonify({"error": message})
    resp.status_code = status_code
    return resp


def _normalize_phone(phone: str) -> str:
    # Keep original characters but trim and collapse whitespace.
    phone = phone.strip()
    phone = re.sub(r"\s+", " ", phone)
    return phone


def _normalize_card(card: str) -> str:
    # Remove spaces and hyphens, common formatting.
    card = card.strip()
    card = re.sub(r"[\s\-]", "", card)
    return card


def _validate_associate_payload(payload: object) -> Tuple[bool, str, str]:
    if not isinstance(payload, dict):
        return False, "", ""

    credit_card = payload.get("credit_card")
    phone = payload.get("phone")

    if not isinstance(credit_card, str) or not credit_card.strip():
        return False, "", ""
    if not isinstance(phone, str) or not phone.strip():
        return False, "", ""

    phone_n = _normalize_phone(phone)
    card_n = _normalize_card(credit_card)

    # Keep validation permissive (tests may use dummy values).
    # But still guard against extremely long inputs.
    if len(phone_n) > 64 or len(card_n) > 64:
        return False, "", ""

    # Basic phone character validation (optional).
    if not _PHONE_RE.match(phone_n):
        # Still allow if it's just digits; some phones may be minimal.
        digits_only = re.sub(r"\D", "", phone_n)
        if len(digits_only) < 3:
            return False, "", ""

    return True, card_n, phone_n


def _validate_retrieve_payload(payload: object) -> Tuple[bool, List[str]]:
    if not isinstance(payload, dict):
        return False, []

    phone_numbers = payload.get("phone_numbers")
    if not isinstance(phone_numbers, list) or not phone_numbers:
        return False, []

    normalized: List[str] = []
    for p in phone_numbers:
        if not isinstance(p, str) or not p.strip():
            return False, []
        pn = _normalize_phone(p)
        if len(pn) > 64:
            return False, []
        normalized.append(pn)

    # Deduplicate while preserving order
    seen = set()
    deduped: List[str] = []
    for pn in normalized:
        if pn not in seen:
            seen.add(pn)
            deduped.append(pn)

    return True, deduped


# -----------------------------
# Routes
# -----------------------------


@app.get("/")
def root():
    return jsonify(
        {
            "service": "Credit Card Phone Association Service",
            "endpoints": ["POST /associate_card", "POST /retrieve_cards"],
        }
    )


@app.post("/associate_card")
def associate_card():
    payload = request.get_json(silent=True)
    ok, card, phone = _validate_associate_payload(payload)
    if not ok:
        return _json_error("Invalid request", 400)

    with STORE.lock:
        STORE.phone_to_cards.setdefault(phone, set()).add(card)

    resp = jsonify({"message": "Association created successfully"})
    resp.status_code = 201
    return resp


@app.post("/retrieve_cards")
def retrieve_cards():
    payload = request.get_json(silent=True)
    ok, phones = _validate_retrieve_payload(payload)
    if not ok:
        return _json_error("Invalid request", 400)

    with STORE.lock:
        # Ensure all phone numbers exist
        missing = [p for p in phones if p not in STORE.phone_to_cards]
        if missing:
            return _json_error("Not found", 404)

        # Intersection across all phones
        intersection: Optional[Set[str]] = None
        for p in phones:
            cards = STORE.phone_to_cards.get(p, set())
            if intersection is None:
                intersection = set(cards)
            else:
                intersection &= cards

        if not intersection:
            return _json_error("Not found", 404)

        # Stable output ordering
        card_numbers = sorted(intersection)

    return jsonify({"card_numbers": card_numbers})


# -----------------------------
# Entry point
# -----------------------------

if __name__ == "__main__":
    # Must listen on 0.0.0.0:5000
    app.run(host="0.0.0.0", port=5000)
