def apply_patch(model, patch_data: dict):
    for field, value in patch_data.items():
        setattr(model, field, value)