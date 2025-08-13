import global_value as g


def has_keywords(message: str, keywords: list[str]) -> bool:
    return next(filter(lambda v: v in message, keywords), None)


def has_keywords_response(message: str) -> bool:
    conf_fa = g.config["fuyukaApi"]
    if not conf_fa:
        return False
    response_keywords = conf_fa["responseKeywords"]
    return has_keywords(message, response_keywords)


def has_keywords_exclusion(message: str) -> bool:
    conf_fa = g.config["fuyukaApi"]
    if not conf_fa:
        return False
    exclusion_keywords = conf_fa["exclusionKeywords"]
    return has_keywords(message, exclusion_keywords)
