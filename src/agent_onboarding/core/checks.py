def passes_aml_screening(identity):
    return identity["family_name"] != "Blocked"
