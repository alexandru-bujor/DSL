from pyparsing import Word, alphanums, nums, Literal, Suppress, Regex, Keyword

# Basic tokens
W = Word(alphanums + "-")
IPV4_ADDRESS = Regex(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
NUMBER = Word(nums)
LBRACE, RBRACE = map(Suppress, "{}")
