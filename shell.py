from pyparsing import (
    Word, alphas, alphanums, Regex, Keyword, Group, ZeroOrMore, nums,
    MatchFirst, ParseException, White
)

# -------------------------------
# Token Patterns
# -------------------------------

# ID: Alphanumeric identifiers with _ and - allowed
ID = Word(alphas + "_", alphanums + "_-").setName("ID")

# Number: Only digits
NUMBER = Word(nums).setName("NUMBER")

# Simple STRING (e.g., words with underscores and spaces)
STRING = Regex(r'"[^"]*"').setName("STRING")

# IP address
IPV4_ADDRESS = Regex(r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}").setName("IPV4_ADDRESS")

# MAC address
MAC_ADDRESS = Regex(r"[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}").setName("MAC_ADDRESS")

# -------------------------------
# Keywords (DSL Commands)
# -------------------------------

keyword_list = [
    "network", "device", "module", "slot", "interface", "vlan", "route", "dhcp",
    "acl", "link", "coordinates", "power", "gateway", "dns", "bandwidth",
    "allow", "deny", "from", "to", "pool", "name", "desc", "cable",
    "length", "functional", "static"
]

# Convert each keyword into a case-sensitive Keyword parser
keywords = [(kw.upper(), Keyword(kw).setName(f"KEYWORD_{kw.upper()}")) for kw in keyword_list]

# -------------------------------
# Combine All Tokens
# -------------------------------

# Token registry (for testing and scanning)
token_definitions = [
        # Match special formats first
        ("IPV4_ADDRESS", IPV4_ADDRESS),
        ("MAC_ADDRESS", MAC_ADDRESS),
        ("STRING", STRING),
        ("NUMBER", NUMBER),

        # Keywords next
] + keywords + [
        # Fallback: generic identifier
        ("ID", ID),
]

# Build a master parser for scanning tokens
token_expr = MatchFirst([
    tok.setParseAction(lambda s, l, t, name=name: (name, t[0]))
    for name, tok in token_definitions
])

# -------------------------------
# Lexer Function
# -------------------------------

def tokenize(text):
    pos = 0
    tokens = []
    while pos < len(text):
        while pos < len(text) and text[pos].isspace():
            pos += 1
        if pos >= len(text):
            break
        try:
            match = list(token_expr.scanString(text[pos:], maxMatches=1))
            if not match:
                raise ParseException(f"Unknown token at position {pos}")
            result, start, end = match[0]
            tokens.append(result[0])  # (TOKEN_TYPE, VALUE)
            pos += end
        except ParseException as pe:
            print(pe)
            break
    return tokens

# -------------------------------
# Optional: Indentation Block Parser
# -------------------------------

def indentedBlock(expr):
    return ZeroOrMore(Group(expr))

# -------------------------------
# Example
# -------------------------------

if __name__ == "__main__":
    sample = 'device router1 interface eth0 ip 192.168.0.1 mac 00ab.cd34.ef56 vlan 10 desc "Main uplink"'

    result = tokenize(sample)
    for token in result:
        print(token)