"""
Tracking ID generation.

Format: LM-XXXXXXX (LM prefix + 7 uppercase alphanumeric chars,
excluding visually ambiguous characters like 0/O and 1/I/L).
Generated and validated for uniqueness by the caller (order_service),
since uniqueness requires a DB round-trip this module doesn't own.
"""
import random
import string

# Excludes 0, O, 1, I, L to avoid ambiguity when read aloud or handwritten
_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


def generate_tracking_id() -> str:
    suffix = "".join(random.choices(_ALPHABET, k=7))
    return f"LM-{suffix}"
