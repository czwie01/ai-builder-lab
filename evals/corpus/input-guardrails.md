# Input guardrails

Guardrails validate what enters a system before the expensive or dangerous parts of the
workflow run. For a question-answering service, that means examining the question at the
boundary and rejecting anything that should never reach retrieval or a model.

## Length limits

Unbounded input is both a cost and a safety problem: very long questions consume tokens,
slow every downstream stage, and are a common vehicle for smuggling instructions. A
maximum length is the cheapest control available and it never has false negatives.

## Control characters

Text arriving over the network may contain null bytes, carriage returns, or terminal
escape sequences that confuse logs, prompts, and anything that renders the value later.
Rejecting control characters at the edge keeps every later stage simpler.

## Injection patterns

Prompt injection tries to get the system to disregard its own instructions by embedding
new ones in user input, with phrasings such as asking the system to ignore what it was
told before. Simple pattern matching catches the obvious attempts cheaply; a classifier
catches more, and neither is sufficient alone.

## Rejecting at the boundary

A guard runs before retrieval, so a rejected question costs nothing beyond the check
itself. Expressing the guard as a port means the policy can grow from a handful of
heuristics into a model-backed classifier without the surrounding workflow noticing.
