def data_access_request(user_id: str) -> dict:
    return load_profile(user_id)


def correct_personal_data(user_id: str, field: str, value: str) -> None:
    update_profile(user_id, field, value)


def delete_account(user_id: str) -> None:
    remove_profile(user_id)


def grievance_officer_contact() -> str:
    return settings.PRIVACY_CONTACT


def nominate_representative(user_id: str, nominee_id: str) -> None:
    save_nominee(user_id, nominee_id)
