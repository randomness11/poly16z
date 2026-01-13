"""
Input validation utilities.
"""

from typing import Optional

from probablyprofit.api.exceptions import ValidationException


def validate_price(price: float, field_name: str = "price") -> float:
    """
    Validate price is between 0 and 1.

    Args:
        price: Price to validate
        field_name: Name of field for error message

    Returns:
        The validated price

    Raises:
        ValidationException: If price is invalid
    """
    if not isinstance(price, (int, float)):
        raise ValidationException(f"{field_name} must be a number, got {type(price)}")

    if price < 0 or price > 1:
        raise ValidationException(f"{field_name} must be between 0 and 1, got {price}")

    return float(price)


def validate_positive(value: float, field_name: str = "value") -> float:
    """
    Validate value is positive.

    Args:
        value: Value to validate
        field_name: Name of field for error message

    Returns:
        The validated value

    Raises:
        ValidationException: If value is invalid
    """
    if not isinstance(value, (int, float)):
        raise ValidationException(f"{field_name} must be a number, got {type(value)}")

    if value <= 0:
        raise ValidationException(f"{field_name} must be positive, got {value}")

    return float(value)


def validate_non_negative(value: float, field_name: str = "value") -> float:
    """
    Validate value is non-negative.

    Args:
        value: Value to validate
        field_name: Name of field for error message

    Returns:
        The validated value

    Raises:
        ValidationException: If value is invalid
    """
    if not isinstance(value, (int, float)):
        raise ValidationException(f"{field_name} must be a number, got {type(value)}")

    if value < 0:
        raise ValidationException(f"{field_name} must be non-negative, got {value}")

    return float(value)


def validate_confidence(confidence: float) -> float:
    """
    Validate confidence is between 0 and 1.

    Args:
        confidence: Confidence value to validate

    Returns:
        The validated confidence

    Raises:
        ValidationException: If confidence is invalid
    """
    return validate_price(confidence, "confidence")


def validate_side(side: str) -> str:
    """
    Validate order side.

    Args:
        side: Order side (BUY or SELL)

    Returns:
        The validated side

    Raises:
        ValidationException: If side is invalid
    """
    if side not in ("BUY", "SELL"):
        raise ValidationException(f"side must be 'BUY' or 'SELL', got '{side}'")

    return side


def validate_private_key(key: str) -> str:
    """
    Validate Ethereum private key format.

    Args:
        key: Private key to validate

    Returns:
        The validated private key

    Raises:
        ValidationException: If key is invalid
    """
    if not isinstance(key, str):
        raise ValidationException("Private key must be a string")

    # Remove 0x prefix if present
    key_clean = key[2:] if key.startswith("0x") else key

    if len(key_clean) != 64:
        raise ValidationException(f"Private key must be 64 hex characters (got {len(key_clean)})")

    try:
        int(key_clean, 16)
    except ValueError:
        raise ValidationException("Private key must be valid hexadecimal")

    return key


def validate_address(address: str) -> str:
    """
    Validate Ethereum address format.

    Args:
        address: Ethereum address to validate

    Returns:
        The validated address

    Raises:
        ValidationException: If address is invalid
    """
    if not isinstance(address, str):
        raise ValidationException("Address must be a string")

    if not address.startswith("0x"):
        raise ValidationException("Address must start with '0x'")

    if len(address) != 42:
        raise ValidationException(f"Address must be 42 characters (got {len(address)})")

    try:
        int(address[2:], 16)
    except ValueError:
        raise ValidationException("Address must be valid hexadecimal")

    return address
