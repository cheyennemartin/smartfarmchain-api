def can_submit_harvest(user):
    if not user.is_authenticated:
        return False

    profile = getattr(user, "profile", None)
    if not profile:
        return False

    return profile.role in ["FARMER", "ADMIN"]


def can_approve_harvest(user, harvest):
    if not user.is_authenticated:
        return False

    profile = getattr(user, "profile", None)
    if not profile:
        return False

    return (
        profile.role in ["ADMIN", "RESEARCH_ORG"]
        and harvest.approval_status == "PENDING"
        and harvest.suspicious_flag is False
    )


def can_reject_harvest(user, harvest):
    if not user.is_authenticated:
        return False

    profile = getattr(user, "profile", None)
    if not profile:
        return False

    return (
        profile.role in ["ADMIN", "RESEARCH_ORG"]
        and harvest.approval_status == "PENDING"
    )


def can_release_payment(user, harvest):
    if not user.is_authenticated:
        return False

    profile = getattr(user, "profile", None)
    if not profile:
        return False

    return (
        profile.role in ["ADMIN", "RESEARCH_ORG"]
        and harvest.approval_status == "APPROVED"
        and harvest.payment_status in ["READY", "PENDING"]
        and harvest.suspicious_flag is False
    )