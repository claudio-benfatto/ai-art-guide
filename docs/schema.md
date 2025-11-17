# Data Schema Documentation

Version: v1.0  
Date: 17 Nov 2025  
Status: MVP Schema Lock

---

## 1. Event Schema

Represents visual art events, exhibitions, and experiences in Barcelona.

### Fields

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| id | string | Yes | Unique event identifier | "evt_001" |
| title_en | string | Yes | English title | "Modern Photography Retrospective" |
| title_es | string | Yes | Spanish title | "Retrospectiva de Fotografía Moderna" |
| description_en | string | Yes | English description (200-800 chars) | "Explore the evolution of..." |
| description_es | string | Yes | Spanish description | "Explora la evolución de..." |
| tags | string[] | Yes | Controlled vocabulary tags | ["modern", "photography", "contemporary"] |
| category | string | Yes | Event category | "gallery", "museum", "street", "pop-up", "opening" |
| domain | string | No | Cultural domain | "visual-art", "music", "theatre", "cinema", "multi" |
| start_date | string | Yes | ISO 8601 date or "unknown" | "2025-11-20", "unknown" |
| end_date | string | Yes | ISO 8601 date or "unknown" | "2025-12-05", "unknown" |
| venue_id | string | Yes | References Venue.id | "v_01" |
| cost_bucket | string | Yes | Cost category or "unknown" | "free", "low" (<10€), "mid" (10-20€), "high" (>20€), "unknown" |
| outdoor | boolean\|string | Yes | Indoor/outdoor or "unknown" | true, false, "unknown" |
| latitude | float | Yes | Geo coordinate | 41.3851 |
| longitude | float | Yes | Geo coordinate | 2.1734 |
| source_type | string | Yes | Data origin | "curated", "external" |
| accessibility_notes | string | No | Optional accessibility info | "Wheelchair accessible" |
| booking_url | string | No | Optional booking link or "unknown" | "https://...", "unknown" |

### Controlled Vocabulary (Tags)

Maximum 30 tags for simplicity; expandable later.

- **Periods/Styles**: modern, contemporary, surrealism, abstract, conceptual, minimalism, baroque, renaissance
- **Media**: photography, painting, sculpture, installation, video, performance, digital, mixed-media
- **Themes**: street, urban, nature, portrait, experimental, political, feminist
- **Audience**: family-friendly, educational, immersive, interactive

### Validation Rules

- `id` must be unique across dataset.
- `start_date` <= `end_date` when both are dates (not "unknown").
- `tags` array length: 2-6 entries.
- `cost_bucket` in allowed set: "free", "low", "mid", "high", "unknown".
- `outdoor` must be boolean (true/false) or string "unknown".
- `domain` (optional) in allowed set: "visual-art", "music", "theatre", "cinema", "multi".
- Coordinates must be within Barcelona bounding box (approx lat 41.3-41.5, lon 2.0-2.3).

---

## 2. Venue Schema

Represents physical or virtual locations hosting events.

### Fields

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| id | string | Yes | Unique venue identifier | "v_01" |
| name | string | Yes | Venue name | "Museu Picasso" |
| type | string | Yes | Venue type | "museum", "gallery", "street-cluster", "cultural-center" |
| neighborhood | string | Yes | Barcelona neighborhood | "El Born" |
| latitude | float | Yes | Geo coordinate | 41.3851 |
| longitude | float | Yes | Geo coordinate | 2.1734 |
| opening_hours | string | No | Freeform text | "Tue-Sun 10:00-19:00" |
| accessibility_notes | string | No | Accessibility info | "Elevator available" |
| url | string | No | Venue website | "https://www.museupicasso.bcn.cat/" |

### Validation Rules

- `id` unique.
- `type` in allowed set.
- Coordinates within Barcelona bounds.

---

## 3. UserProfile Schema

Stores user preferences and interaction history (Firestore document).

### Fields

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| user_id | string | Yes | Unique user identifier (UUID) | "usr_abc123" |
| preferred_tags | object | Yes | Tag weights (1-5 scale) | {"modern": 5, "photography": 4} |
| saved_event_ids | string[] | Yes | Bookmarked events | ["evt_001", "evt_003"] |
| language | string | Yes | Preferred language | "en", "es" |
| last_interaction_ts | string | Yes | ISO 8601 timestamp | "2025-11-17T14:30:00Z" |
| created_at | string | Yes | ISO 8601 timestamp | "2025-11-15T10:00:00Z" |

### Validation Rules

- `user_id` unique.
- `preferred_tags` keys must be in controlled vocabulary.
- `preferred_tags` values: integers 1-5.
- `language` in ["en", "es"].

---

## 4. EmbeddingDoc Schema

Stores precomputed embeddings for events (JSON file or future vector DB).

### Fields

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| event_id | string | Yes | References Event.id | "evt_001" |
| text_concat | string | Yes | Concatenated text for embedding | "Modern Photography...tags:modern,photography" |
| vector | float[] | Yes | Embedding vector | [0.123, -0.456, ...] (dim 384 or 768) |
| tags | string[] | Yes | Copy of event tags for filtering | ["modern", "photography"] |
| version | string | Yes | Embedding model version | "v1_text-multilingual-embedding-002" |

### Validation Rules

- `event_id` unique; must exist in events dataset.
- `vector` dimension consistent across all entries.
- `version` tracked for re-embedding trigger.

---

## 5. Context Object (Runtime, Not Persisted)

Shared state passed between agents during a conversation turn.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| user_id | string | Current user identifier |
| language | string | User's preferred language |
| recent_utterances | string[] | Last 5 user utterances |
| summary | string or None | Conversation summary (generated every 3 turns) |
| user_profile | object | Loaded UserProfile (preferred_tags, saved_event_ids) |
| recent_recommended_ids | string[] | Last recommended event IDs for novelty calc |
| turn_id | int | Current turn number |
| degraded_mode | bool | True if operating in fallback mode (no Vertex) |

---

## 6. AgentResponse Object (Internal)

Returned by each agent after processing.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| updated_context | object | Partial updates to Context object |
| payload | object | Agent-specific output (e.g., candidate events, ranked recommendations) |
| errors | object[] | Structured error codes if any |

---

## 7. Settings Schema (YAML Config)

Configuration for scoring weights, model IDs, thresholds.

### Example

```yaml
version: "1.0"
embedding:
  model_id: "text-multilingual-embedding-002"
  dimension: 768
  batch_size: 100

scoring:
  weights:
    cosine: 0.5
    tag_overlap: 0.2
    novelty: 0.2
    temporal_fit: 0.1
  diversity:
    max_same_venue: 1

memory:
  decay_lambda: 0.02
  summary_frequency: 3

retrieval:
  max_results: 12
  default_geo_radius_km: 5.0

controlled_vocabulary:
  - modern
  - contemporary
  - photography
  - painting
  - sculpture
  - installation
  - street
  - abstract
  - surrealism
  - conceptual
  - minimalism
  - performance
  - digital
  - mixed-media
  - urban
  - nature
  - portrait
  - experimental
  - political
  - feminist
  - family-friendly
  - educational
  - immersive
  - interactive
  - baroque
  - renaissance
  - video
```

---

## 8. Data Versioning

All data files and schemas are versioned:
- `events_v1.json`
- `embeddings_v1.json`
- Schema version tracked in `settings.yaml`

When schema changes:
1. Increment version.
2. Create migration script if needed.
3. Re-validate all data.
4. Re-embed if text_concat format changes.

---

## 9. Data Quality Constraints

- **Completeness**: Required fields must have non-empty values.
- **Uniqueness**: IDs must be unique within type.
- **Referential Integrity**: `venue_id` in Event must exist in Venue dataset; `event_id` in EmbeddingDoc must exist in Event dataset.
- **Temporal Consistency**: `start_date` <= `end_date`.
- **Tag Validity**: All tags must be in controlled vocabulary.
- **Geo Bounds**: Coordinates must be within Barcelona metropolitan area.

---

## 10. Future Schema Extensions (Post-MVP)

- **Artist Schema**: artist_id, name, bio, style_tags, related_event_ids.
- **Graph Edges**: artist-event, artist-style, venue-neighborhood relationships.
- **Image Embeddings**: Add image_vector to Event for multimodal retrieval.
- **User Feedback**: Add rating, attended (bool), feedback_text to interaction log.
- **Calendar Integration**: Add ical_uid, google_calendar_event_id.

---

End of schema documentation.
