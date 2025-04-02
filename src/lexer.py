from pyparsing import (
    Word,
    alphas,
    alphanums,
    Regex,
    Keyword,
    nums,
    Suppress,
    MatchFirst,
    ParseException,
)

# -------------------------------------------------
# CORE TOKENS
# -------------------------------------------------

# ID: Alphanumeric identifiers with underscores/hyphens
ID = Word(alphas + "_", alphanums + "_-").setName("ID")

# Number: Only digits
NUMBER = Word(nums).setName("NUMBER")

# Simple STRING (words in quotes)
STRING = Regex(r'"[^"]*"').setName("STRING")

# IP address
IPV4_ADDRESS = Regex(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b').setName("IPV4_ADDRESS")

# MAC address
MAC_ADDRESS = Regex(r'[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}').setName("MAC_ADDRESS")

# A word token (letters/digits/hyphens)
W = Word(alphanums + "-")

# Braces
LBRACE, RBRACE = map(Suppress, "{}")

# -------------------------------------------------
# KEYWORDS
# -------------------------------------------------
keyword_list = [
    "network", "device", "module", "slot", "interface", "vlan", "route", "dhcp",
    "acl", "link", "coordinates", "power", "gateway", "dns", "bandwidth",
    "allow", "deny", "from", "to", "pool", "name", "desc", "cable",
    "length", "functional", "static"
]

# Build Pyparsing Keyword objects for each
keywords = [
    (kw.upper(), Keyword(kw).setName(f"KEYWORD_{kw.upper()}"))
    for kw in keyword_list
]

# -------------------------------------------------
# OPTIONAL: TOKEN SCANNER
# -------------------------------------------------
# If you want a separate token-scanning approach (like in shell.py),
# you can define a master MatchFirst expression that tries each token.

token_definitions = [
    ("IPV4_ADDRESS", IPV4_ADDRESS),
    ("MAC_ADDRESS", MAC_ADDRESS),
    ("STRING", STRING),
    ("NUMBER", NUMBER),
] + keywords + [
    ("ID", ID),
]

token_expr = MatchFirst([
    tok.setParseAction(lambda s, l, t, name=name: (name, t[0]))
    for name, tok in token_definitions
])

def tokenize(text):
    """
    Converts raw DSL text into a list of (TOKEN_TYPE, VALUE) pairs,
    using the token definitions above.
    """
    pos = 0
    tokens = []
    length = len(text)

    while pos < length:
        # Skip whitespace
        while pos < length and text[pos].isspace():
            pos += 1
        if pos >= length:
            break

        try:
            match_data = list(token_expr.scanString(text[pos:], maxMatches=1))
            if not match_data:
                raise ParseException(f"Unknown token at position {pos}")
            result, start, end = match_data[0]
            tokens.append(result[0])  # (TOKEN_TYPE, VALUE)
            pos += end
        except ParseException as pe:
            print(pe)
            break
    return tokens
