"""
Distillation: hallucinated claim -> realistic core -> heroic goal.

The directive this implements: nothing that was previously dismissed as
hallucination gets thrown away. It gets *reduced*. Every claim is stripped
down to the part of it that could actually be wrong, and only that part is
allowed to become a goal. Then -- and only then -- the goal is backed with
code.

The reduction is rule-based and deterministic, not model-driven, for one
reason: this module's own output is checked by the totem, and a totem that
consults a language model will spin forever. The same claim must always
distill to the same core, on any machine, in any year.

The three stages
----------------
1. ``raw_claim``      -- the sentence as written, rhetoric and all.
2. ``realistic_core`` -- the same sentence with every unfalsifiable
   intensifier removed. What remains is what was actually asserted.
3. ``heroic_goal``    -- the core restated against an acceptance criterion,
   i.e. the precise observation that would prove it.

A claim with no acceptance criterion produces no heroic goal. That is not
an error and not a rejection: it is the honest outcome for a sentence that
cannot be wrong. Such archives are recorded, kept, and left in limbo.
"""

from __future__ import annotations

import re
import unicodedata

from .models import Distillation

#: Words that raise the temperature of a sentence without adding anything a
#: machine could check. Removing them is lossless with respect to truth: no
#: observation can distinguish "advanced QUBO solving" from "QUBO solving".
UNVERIFIABLE_INTENSIFIERS: frozenset[str] = frozenset(
    {
        # English
        "advanced", "comprehensive", "complete", "completely", "cutting-edge",
        "deep", "deeper", "effortless", "elegant", "enterprise-grade",
        "flawless", "full", "fully", "groundbreaking", "industry-leading",
        "infinite", "limitless", "major", "next-generation", "perfect",
        "powerful", "production-grade", "production-ready", "revolutionary",
        "robust", "seamless", "seamlessly", "significant", "significantly",
        "state-of-the-art", "strong", "stronger", "unlimited", "unmatched",
        "unprecedented", "world-class",
        # German
        "bahnbrechend", "beeindruckend", "endlos", "gewaltig", "grenzenlos",
        "hochmodern", "kraftvoll", "legendär", "maximal", "mächtig",
        "nahtlos", "perfekt", "radikal", "revolutionär", "umfassend",
        "unendlich", "vollständig", "vollumfänglich", "wegweisend",
    }
)

#: Phrases that promise a future rather than describe a present. A claim
#: containing one of these is not about anything that exists yet.
FUTURE_MARKERS: frozenset[str] = frozenset(
    {"planned", "coming soon", "will be", "roadmap", "geplant", "demnächst", "zukünftig"}
)

_WORD = re.compile(r"[\w\-äöüßÄÖÜ]+", re.UNICODE)
_WHITESPACE = re.compile(r"\s+")
_PUNCT_GAP = re.compile(r"\s+([,.;:!?])")


def _normalize(text: str) -> str:
    """NFKC-normalize and collapse whitespace so distillation is stable."""
    return _WHITESPACE.sub(" ", unicodedata.normalize("NFKC", text)).strip()


def strip_intensifiers(claim: str) -> tuple[str, tuple[str, ...]]:
    """
    Remove unfalsifiable intensifiers, preserving everything else verbatim.

    Returns the reduced sentence and the terms that were dropped, in the
    order they appeared. The dropped terms are kept in the record: the
    protocol reduces claims, it does not silently rewrite history.
    """
    dropped: list[str] = []

    def replace(match: re.Match[str]) -> str:
        word = match.group(0)
        if word.casefold() in UNVERIFIABLE_INTENSIFIERS:
            dropped.append(word)
            return ""
        return word

    reduced = _WORD.sub(replace, _normalize(claim))
    reduced = _PUNCT_GAP.sub(r"\1", _WHITESPACE.sub(" ", reduced)).strip()
    reduced = reduced.strip(" -–—,;")

    # If nothing but punctuation survived, the sentence was rhetoric all the
    # way down. There is no core to keep, and "..." is not one.
    if not _WORD.search(reduced):
        return "", tuple(dropped)

    if reduced and reduced[0].islower():
        reduced = reduced[0].upper() + reduced[1:]

    return reduced, tuple(dropped)


def has_future_marker(claim: str) -> bool:
    """True when the claim describes an intention rather than a fact."""
    folded = _normalize(claim).casefold()
    return any(marker in folded for marker in FUTURE_MARKERS)


def distill(claim: str, acceptance: str | None = None) -> Distillation:
    """
    Reduce one claim to its realistic core and, where possible, a heroic goal.

    ``acceptance`` is the observation that would settle the claim -- the
    thing a machine could go and check. Supply it and the claim becomes a
    heroic goal that code can be held to. Omit it, or describe something
    that has not been built yet, and the claim stays a dream.
    """
    raw = _normalize(claim)
    if not raw:
        raise ValueError("cannot distill an empty claim")

    core, dropped = strip_intensifiers(raw)
    if not core:
        # The sentence was nothing but rhetoric; there is no core to keep.
        return Distillation(raw_claim=raw, realistic_core="", heroic_goal=None, dropped_terms=dropped)

    criterion = _normalize(acceptance) if acceptance else ""
    if not criterion or has_future_marker(raw) or has_future_marker(criterion):
        return Distillation(
            raw_claim=raw, realistic_core=core, heroic_goal=None, dropped_terms=dropped
        )

    goal = f"{core.rstrip('.')} — nachweisbar durch: {criterion.rstrip('.')}"
    return Distillation(
        raw_claim=raw, realistic_core=core, heroic_goal=goal, dropped_terms=dropped
    )
