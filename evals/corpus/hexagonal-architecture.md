# Hexagonal architecture

Hexagonal architecture, also called ports and adapters, separates the part of a system
that encodes business rules from the parts that talk to the outside world. The rules live
in the middle and know nothing about how they are reached or where their data comes from.

## Ports

A port is an interface the application core depends on. It is written in the language of
the core, not of the technology behind it: a retrieval port speaks of queries and results,
never of collections, indexes, or HTTP calls. In Python a port is naturally expressed as a
`Protocol`, which lets implementations satisfy it structurally without importing it, so
every dependency arrow keeps pointing inward.

## Adapters

An adapter is a concrete implementation of a port, wired in from the outside. All
infrastructure lives here: database clients, vendor SDKs, network calls, filesystem
access. Because the core only sees the port, one adapter can be exchanged for another
without editing a single line of business logic.

## The composition root

Adapters are bound to ports in exactly one place, the composition root. Keeping the
wiring in a single module is what makes substitution cheap and auditable: to learn which
implementation is active you read one file, and to change it you edit one file. A test can
override the same bindings to run the whole system against fakes.

## Why it pays off for AI systems

Machine learning infrastructure changes faster than business requirements. Vector
databases, embedding models, model vendors, and agent frameworks all turn over on a
timescale of months. When each of them sits behind a port, that churn becomes an adapter
swap instead of a rewrite, and the tests that describe behaviour keep passing untouched.
