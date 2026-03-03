Tokenization and normalization
This is the simplest layer, but it’s foundational. The relevant ideas are:

Whitespace tokenization — exactly what you’re doing now.

Case folding — lowercasing everything.

Punctuation stripping — remove trailing punctuation (“look,” → “look”).

Span tracking — record start/end indices for each token.

These are trivial to implement but essential for building the token_spans field.

Lexical lookup and longest‑match scanning
This is the first “real” algorithmic idea you’ll use.

Why it matters
You want to support:

multiword verbs (“pick up”, “put out”, “look at”)

multiword nouns (“treasure chest”, “north wall”)

multiword modifiers (“in front of”, “on top of”)

The algorithm
Use a greedy longest‑match scan:

Start at token i.

Try to match the longest possible sequence of tokens against the lexicon.

If a multiword match exists, take it.

Otherwise, fall back to single‑token matching.

This is a classic technique used in:

early text adventures

command interpreters

shallow NLP pipelines

It’s simple, deterministic, and perfect for your needs.

Chunking: grouping tokens into phrases
This is where your parser starts to feel like a real parser, but you still don’t need grammar theory.

The relevant idea is shallow parsing, also called chunking.

Why it matters
You want to produce:

noun phrases

prepositional phrases

conjunction groups

The algorithm
Use a finite‑state chunker:

When you see a noun → start a noun phrase.

When you see an adjective → attach it to the next noun.

When you see a preposition → start a prepositional phrase.

When you see a conjunction → start a conjunction group.

This is not a full parse tree. It’s a flat, shallow structure — exactly what your ParsedSyntax contract calls for.

This is the same technique used in:

early NLP toolkits

rule‑based chatbots

classic IF parsers (Zork, Inform 6)

Ambiguity preservation
This is one of the most important ideas in your architecture.

Why it matters
Tokens like “in”, “out”, “up”, “down” can be:

directions

modifiers

adverbs

prepositions

The parser must not decide which meaning is correct.

The algorithm
Use parallel tagging:

For each token, record all categories it could belong to.

Do not collapse them.

Pass the ambiguity to the resolver.

This is exactly how:

Inform 6

TADS 3

modern NLP taggers

handle ambiguous tokens.

Prepositional phrase attachment
This is where many parsers get complicated, but you don’t need to.

Why it matters
You want to support:

“look in the box”

“take all from the bag”

“go through the door”

The algorithm
Use right‑branching attachment:

A preposition attaches to the nearest following noun phrase.

If none exists yet, create an empty placeholder.

This is simple, predictable, and matches how classic IF engines behave.

Conjunction handling
This is another place where you can use a simple, robust algorithm.

Why it matters
You want to support:

“take apple and banana”

“drop sword, shield, and helmet”

The algorithm
Use flat conjunction groups:

When you see “and” or “,” → start a new group.

Group all noun phrases under the same verb.

This avoids building a tree and keeps the resolver’s job simple.

Diagnostics and unknown tokens
This is not an algorithm so much as a pattern.

Why it matters
You want to:

preserve unknown tokens

record parser decisions

help the resolver and renderer produce good messages

The algorithm
Maintain a diagnostic log:

“unknown token: frobnicate”

“ambiguous token: in (modifier, direction)”

“multiword match: ‘put out’ → verb”

This is extremely helpful for debugging and for future features like “parser help mode.”

Why you don’t need full parsing theory
You do not need:

context‑free grammars

parser generators

LR/LALR/Earley/GLR parsers

ASTs

semantic actions

unification grammars

dependency parsing

Those tools solve problems you don’t have.

Your domain is:

short commands

predictable structure

small vocabulary

shallow syntax

no recursion

no nested clauses

A lightweight, rule‑based, shallow parser is exactly the right tool.

The algorithms that matter most for your engine
Here’s the short list:

Greedy longest‑match lexeme scanning

Finite‑state chunking for noun/prep phrases

Parallel tagging for ambiguous tokens

Right‑branching prepositional attachment

Flat conjunction grouping

Diagnostic logging

These are the same techniques used in:

Zork / Infocom

Inform 6

TADS 2/3

Dialog

Scott Adams engines

Modern command interpreters

You’re in excellent company.