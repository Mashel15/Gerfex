# Legacy provider loader disabled by Gerfex Intelligence Gateway policy.
#
# Official model boundary:
# internal_intelligence/gerfex_entry_gate/
#
# No Gerfex component should load GMA/provider/runtime directly from here.


def set_active_provider_name(name):
    return {
        "ok": False,
        "reason": "legacy_provider_loader_disabled_by_gateway_policy",
        "requested_provider": name,
    }


def get_active_provider_name():
    return None


def load_provider(name=None):
    raise RuntimeError(
        "legacy_provider_loader_disabled_by_gateway_policy: "
        "use internal_intelligence.gerfex_entry_gate instead"
    )
