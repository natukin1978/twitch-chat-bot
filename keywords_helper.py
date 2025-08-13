import global_value as g


def has_keywords_response(message: str) -> bool:
    conf_fa = g.config["fuyukaApi"]
    if not conf_fa:
        return False
    response_keywords = conf_fa["responseKeywords"]
    return next(filter(lambda v: v in message, response_keywords), None)


def has_keywords_exclusion(message: str) -> bool:
    conf_fa = g.config["fuyukaApi"]
    if not conf_fa:
        return False
    exclusion_keywords = conf_fa["exclusionKeywords"]
    return next(filter(lambda v: v in message, exclusion_keywords), None)
