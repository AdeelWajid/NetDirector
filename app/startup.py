def select_startup_profile(profiles, settings, discovery_complete):
    if not discovery_complete:
        return None
    if settings["load_startup"]:
        selected = [p for p in profiles if p.startup]
        if len(selected) > 1:
            raise ValueError("Multiple startup profiles are selected. Choose one in Profiles.")
        if selected:
            return selected[0]
    if settings["restore_active"]:
        return next((p for p in profiles if p.id == settings["last_profile"]), None)
    return None
