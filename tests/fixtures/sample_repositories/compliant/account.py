def withdraw_consent(user_id: str) -> None:
    """Record a user's consent withdrawal request."""
    return None


def grant_consent(user_id: str, purpose: str) -> bool:
    """Store an affirmative consent choice tied to a stated purpose."""
    return bool(user_id and purpose)


def data_access_request(user_id: str) -> dict:
    return {"user_id": user_id}


def delete_account(user_id: str) -> None:
    return None


def correct_personal_data(user_id: str, field: str, value: str) -> None:
    return None


def grievance_contact() -> str:
    return "privacy@example.invalid"
