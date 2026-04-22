from __future__ import annotations

import re
from dataclasses import dataclass, field

from models.llm_response import BeatCandidate, LLMResponse


_STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "at", "for",
    "with", "by", "from", "into", "through", "your", "you", "their", "his",
    "her", "its", "is", "are", "was", "were", "be", "been", "this", "that",
    "it", "as", "but", "not", "have", "has", "had", "about", "after", "before",
    "current", "quest", "beat", "story", "main"
}


@dataclass
class SelectedBeat:
    summary: str
    importance: int = 1
    beat_type: str = "main"
    tags: list[str] = field(default_factory=list)
    score: float = 0.0


class EventSelector:
    """Select a focused story beat so turns stay tied to a main thread."""

    _TYPE_BONUS = {
        "main": 3.0,
        "reveal": 2.0,
        "complication": 1.8,
        "stakes": 1.8,
        "world": 1.0,
        "side": -0.5,
        "vignette": -1.0,
    }

    def select(
        self,
        response: LLMResponse,
        quest: dict | None = None,
        story_beats: str = "",
        action: str = "",
    ) -> SelectedBeat | None:
        candidates = self._candidates_from_response(response)
        if not candidates:
            return None

        context = " ".join(part for part in [action, story_beats, self._quest_text(quest)] if part)
        scored = [self._score_candidate(candidate, context) for candidate in candidates]
        scored.sort(key=lambda item: item.score, reverse=True)
        chosen = scored[0]

        response.selected_beat = BeatCandidate(
            summary=chosen.summary,
            beat_type=chosen.beat_type,
            importance=chosen.importance,
            tags=chosen.tags,
            weight=max(0.1, chosen.score),
        )
        response.important_beat = chosen.summary
        return chosen

    def _candidates_from_response(self, response: LLMResponse) -> list[BeatCandidate]:
        if response.candidate_beats:
            return response.candidate_beats

        summary = response.important_beat or response.state_update.important_beat
        if not summary:
            return []

        return [BeatCandidate(summary=summary, beat_type="main", importance=1, weight=1.0)]

    def _score_candidate(self, candidate: BeatCandidate, context: str) -> SelectedBeat:
        summary = candidate.summary.strip()
        base = float(candidate.importance) * 1.5 + float(candidate.weight)
        type_bonus = self._TYPE_BONUS.get(candidate.beat_type.lower(), 0.0)
        overlap = self._overlap_score(summary, context)
        tag_bonus = 0.5 * self._overlap_score(" ".join(candidate.tags), context)

        score = base + type_bonus + overlap + tag_bonus
        if len(summary) < 20:
            score -= 0.5
        if not context:
            score += 0.5

        return SelectedBeat(
            summary=summary,
            importance=max(1, int(candidate.importance)),
            beat_type=candidate.beat_type or "main",
            tags=list(candidate.tags),
            score=round(score, 3),
        )

    def _quest_text(self, quest: dict | None) -> str:
        if not quest:
            return ""
        title = str(quest.get("title", ""))
        objective = str(quest.get("objective", ""))
        hints = ", ".join(quest.get("hints", [])) if isinstance(quest.get("hints", []), list) else ""
        return " ".join(part for part in [title, objective, hints] if part)

    def _overlap_score(self, text: str, context: str) -> float:
        text_tokens = self._tokens(text)
        context_tokens = self._tokens(context)
        if not text_tokens or not context_tokens:
            return 0.0
        overlap = len(text_tokens & context_tokens)
        if overlap == 0:
            return 0.0
        return min(3.0, overlap * 0.75)

    def _tokens(self, text: str) -> set[str]:
        tokens = {token for token in re.findall(r"[a-z0-9']+", text.lower()) if token not in _STOPWORDS}
        return tokens