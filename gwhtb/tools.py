def markdown_char_escape(string_to_scape: str) -> str:
    for char in [
        "_",
        "*",
        "[",
        "]",
        "(",
        ")",
        "~",
        "`",
        ">",
        "#",
        "+",
        "-",
        "=",
        "|",
        "{",
        "}",
        ".",
        "!",
    ]:
        string_to_scape = string_to_scape.replace(char, f"\{char}")

    return string_to_scape
