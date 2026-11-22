def grant_consent(user_id: str, purpose: str) -> None:
    save_consent(user_id, purpose)


def withdraw_consent(user_id: str) -> None:
    revoke_consent(user_id)
