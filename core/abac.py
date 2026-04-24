def get_profile(user):
    if not user.is_authenticated:
        return None

    return getattr(user, "profile", None)


def wallet_matches(user, wallet_address):
    profile = get_profile(user)

    if not profile:
        return False

    if not profile.wallet_address or not wallet_address:
        return False

    return profile.wallet_address.lower() == wallet_address.lower()


def can_submit_harvest(user, wallet_address):
    profile = get_profile(user)

    return (
        profile is not None
        and profile.role in ["FARMER", "ADMIN"]
        and wallet_matches(user, wallet_address)
    )


def can_analyze_data(user, wallet_address):
    profile = get_profile(user)

    return (
        profile is not None
        and profile.role in ["RESEARCH_ORG", "ADMIN"]
        and wallet_matches(user, wallet_address)
    )


def can_approve_harvest(user, harvest, wallet_address):
    profile = get_profile(user)

    return (
        profile is not None
        and profile.role == "ADMIN"
        and wallet_matches(user, wallet_address)
        and harvest.approval_status == "PENDING"
        and harvest.suspicious_flag is False
    )


def can_reject_harvest(user, harvest, wallet_address):
    profile = get_profile(user)

    return (
        profile is not None
        and profile.role == "ADMIN"
        and wallet_matches(user, wallet_address)
        and harvest.approval_status == "PENDING"
    )


def can_release_payment(user, harvest, wallet_address):
    profile = get_profile(user)

    return (
        profile is not None
        and profile.role == "ADMIN"
        and wallet_matches(user, wallet_address)
        and harvest.approval_status == "APPROVED"
        and harvest.payment_status in ["READY", "PENDING"]
        and harvest.suspicious_flag is False
    )


def can_view_harvest(user, harvest, wallet_address):
    profile = get_profile(user)

    if not profile:
        return False

    if not wallet_matches(user, wallet_address):
        return False

    if profile.role in ["ADMIN", "RESEARCH_ORG"]:
        return True

    return harvest.farmer == user