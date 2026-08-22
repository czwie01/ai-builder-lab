# Observability at the edge

Observability answers what happened during a request after the fact. The information it
needs — identifiers, timings, statuses — belongs to the delivery mechanism, not to the
business rules, so it is collected at the edge and never threaded through the core.

## Request identifiers

Each request carries an identifier, either supplied by the caller in a header or generated
on arrival, and it is echoed back in the response. Everything logged while handling that
request carries the same identifier, so a single line in a log file leads to the whole
story of one call.

## Context variables

A context variable holds the current request's identifier for the duration of the call,
which lets a log formatter attach it automatically. Nothing in the domain or application
layer has to accept, store, or pass along a tracing parameter, so those layers contain no
observability code at all.

## Structured logs

Logs emitted as structured records rather than prose can be filtered and aggregated
without parsing. A useful access record carries the identifier, the route, the response
status, and how long the call took, which is enough to find slow paths and failures.

## Latency and cost

Recording how long each stage takes shows where time actually goes: retrieval, model
inference, or the network in between. Once a model is involved, token counts and cache
hit rates belong beside latency, because they are what the bill is made of.
