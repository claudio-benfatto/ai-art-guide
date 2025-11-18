#!/usr/bin/env python
from __future__ import annotations
import json, os, sys
from pathlib import Path
from typing import List, Dict
import yaml

# Allow running as script without installing package
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from adk.rag.embeddings import get_embeddings

EVENTS_FILE = Path('data/events.yaml')
OUT_FILE = Path('data/embeddings_v1.json')
MODEL = os.environ.get('EMBEDDINGS_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
PROVIDER = os.environ.get('EMBEDDINGS_PROVIDER', 'hf')


def load_events() -> List[Dict]:
    data = yaml.safe_load(EVENTS_FILE.read_text())
    events = data.get('events', [])
    # Compose text_concat field
    for e in events:
        parts = [e.get('title_en',''), e.get('description_en',''), ', '.join(e.get('tags', []))]
        e['text_concat'] = '\n'.join([p for p in parts if p])
    return events


def main():
    events = load_events()
    emb_provider = get_embeddings(provider=PROVIDER, model_name=MODEL)
    texts = [e['text_concat'] for e in events]
    vectors = emb_provider.embed_batch(texts)
    dim = len(vectors[0]) if vectors else 0
    docs = []
    for e, vec in zip(events, vectors):
        docs.append({
            'event_id': e['id'],
            'embedding': vec,
            'tags': e.get('tags', []),
            'text_concat': e['text_concat'],
            'start_date': str(e.get('start_date', 'unknown')),
            'end_date': str(e.get('end_date', 'unknown')),
            'latitude': e.get('latitude'),
            'longitude': e.get('longitude'),
        })
    payload = {
        'schema_version': 1,
        'embedding_model': emb_provider.model_name,
        'provider': emb_provider.provider,
        'dim': dim,
        'docs': docs,
    }
    OUT_FILE.write_text(json.dumps(payload, indent=2))
    print(f'Wrote {len(docs)} embeddings to {OUT_FILE} (dim={dim}, provider={emb_provider.provider})')

if __name__ == '__main__':
    main()
