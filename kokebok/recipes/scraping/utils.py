import bs4


def recursive_strip_attrs(tag: bs4.Tag, attrs: list[str] | None) -> bs4.Tag:
    """
    Strips the given attrs from the tag and all its descendants.
    If the arguments attrs list is empty or None, all attrs are removed.
    Returns the tag for convenience.
    """

    def strip_attrs(tag: bs4.Tag, attrs: list[str] | None) -> bs4.Tag:
        for attr in attrs or list(tag.attrs.keys()):
            del tag[attr]
        return tag

    strip_attrs(tag, attrs)
    for child in tag.descendants:
        if isinstance(child, bs4.Tag):
            strip_attrs(child, attrs)
    return tag
