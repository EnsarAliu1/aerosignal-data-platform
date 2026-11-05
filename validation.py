import re

def validate_ingestion_params(
    year: int,
    month: int,
    source_sha256: str,
) -> None:
    """
    Validate ingestion parameters.
    Raise ValueError for invalid input.
    """

    if not isinstance(year, int) or not 1987 <= year <= 2100:
        raise ValueError("Invalid year")

    if not isinstance(month, int) or not 1 <= month <= 12:
        raise ValueError("Month must be between 1 and 12")

    if not re.fullmatch(r"[a-fA-F0-9]{64}", source_sha256):
        raise ValueError("Invalid SHA256")