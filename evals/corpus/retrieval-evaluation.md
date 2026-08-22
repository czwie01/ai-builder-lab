# Evaluating retrieval

Retrieval is evaluated by running a fixed set of questions with known answers through the
system and measuring how often the right sources come back. Without such a measurement,
every change to the pipeline is a guess.

## Golden datasets

A golden dataset pairs each question with the identifiers of the documents that genuinely
answer it. It grows from three sources: hand-written cases covering known edge conditions,
real questions observed in use, and synthetic expansions reviewed by a human before they
are trusted. Every bug worth fixing becomes a new case.

## Recall at k

Recall at k asks what fraction of the relevant documents appear in the first k results.
It is the measure that matters first, because later stages can only reorder what was
already fetched: a result that never entered the candidate set cannot be rescued.

## Mean reciprocal rank

Mean reciprocal rank averages one divided by the position of the first correct result. It
rewards putting the right source at the top rather than merely somewhere in the list, and
it complements recall, which is indifferent to ordering within the cutoff.

## Thresholds and honesty

Metrics become a gate when a change that lowers them fails the build. The discipline that
makes the gate meaningful is refusing to loosen a threshold quietly: a threshold may move
when the corpus or the question set changes, but the reason belongs in the commit message,
and the measurement must be taken before the number is chosen.

## Corpus size matters

A gate over a tiny corpus measures very little. When three results are returned from a
four-document collection, even random selection scores well, and a single flipped question
swings the average by an eighth. A meaningful gate needs enough documents that being
correct is genuinely harder than guessing.
