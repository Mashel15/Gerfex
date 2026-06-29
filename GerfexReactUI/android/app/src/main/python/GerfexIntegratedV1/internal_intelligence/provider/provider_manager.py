ACTIVE_PROVIDER = None


def set_provider(provider):
    global ACTIVE_PROVIDER
    ACTIVE_PROVIDER = provider


def get_provider():
    return ACTIVE_PROVIDER


def provider_name():
    if ACTIVE_PROVIDER is None:
        return "none"

    return getattr(ACTIVE_PROVIDER, "PROVIDER_NAME", "unknown")


def provider_available():
    return ACTIVE_PROVIDER is not None
