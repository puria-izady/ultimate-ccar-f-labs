"""The three documents the research tools serve.

Short on purpose. These exist to give the tools something to answer with, not to be
studied, and the retrieval below is a set intersection rather than a scorer for the
same reason: the lab is about the technique, not about retrieval quality.

Each document is rigged so that one section of the report fills from a different place.

| Section | What fills it |
|---|---|
| Well established | Visual art, where the published source stands on its own |
| Contested | Music, where the two channels report different figures |
| Coverage gaps | The internal channel holds nothing on visual art |

The music pair disagree because they counted different populations over windows that do
not overlap: one counted nineteen studios over eight months and excluded home studios,
the other counted every project in a quarter and included them. Neither is wrong, which
is why the report has to keep both.
"""

from __future__ import annotations

__all__ = ["DOCS", "BY_URL", "FIELD_WORDS", "FIELDS"]

DOCS = [
    {"field": "visual_art", "channel": "web",
     "url": "https://riverbend-design-review.example/2026/02/illustration-studios",
     "title": "Illustration studios and generated concept art",
     "publisher": "Riverbend Design Review",
     "publication_date": "2026-02-11", "collection_period": "2025-01 to 2025-09",
     "text": "Across forty-two studios, commissioning of external concept art fell by twelve "
             "per cent against the previous comparable period. The decline is concentrated "
             "in early-stage mood and layout work rather than in finished illustration, and "
             "studios reported that revision rounds rose over the same window."},
    {"field": "music", "channel": "web",
     "url": "https://riverbend-music-quarterly.example/2026/01/session-players",
     "title": "Session players and generated stems",
     "publisher": "Riverbend Music Quarterly",
     "publication_date": "2026-01-09", "collection_period": "2025-03 to 2025-10",
     "text": "Booking logs from nineteen recording studios show total session hours down by "
             "nine per cent against the previous comparable period. The decline is "
             "concentrated in library and advertising work rather than in album sessions. "
             "The analysis excludes home and project studios."},
    {"field": "music", "channel": "internal",
     "url": "https://intranet.example/post-production/2026/01/audio-post-note",
     "title": "Audio post production note",
     "publisher": "Post Production, internal",
     "publication_date": "2026-01-30", "collection_period": "Q4 2025",
     "text": "Session hours booked across the quarter fell by twenty-two per cent against "
             "the same quarter a year earlier. The review counts every project the "
             "department ran, including work recorded in home and project studios."},
]

# A search snippet is the opening of the document, so it is derived rather than stored twice.
for _doc in DOCS:
    _doc["excerpt"] = _doc["text"].split(". ")[0] + "."

BY_URL = {doc["url"]: doc for doc in DOCS}

FIELDS = [{"id": "visual_art", "label": "visual art and design"},
          {"id": "music", "label": "music and audio"}]

# What a field is called when somebody asks about it. Matching whole words against this
# set keeps the lab about the technique rather than about retrieval quality.
FIELD_WORDS = {
    "visual_art": frozenset("visual art arts design designs illustration illustrations "
                            "concept gallery galleries studio studios".split()),
    "music": frozenset("music musical audio session sessions stem stems track tracks "
                       "recording recordings player players".split()),
}
