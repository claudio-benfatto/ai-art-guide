# Data Entry Guide for Product Managers

Welcome! This guide will help you add and edit events and venues for the Barcelona AI Art Guide.

## Quick Start

1. **Open the data file**: `data/events.yaml`
2. **Edit in your favorite text editor** (VS Code recommended)
3. **Save your changes**
4. **Validate**: Run `python scripts/validate_events_pydantic.py data/events.yaml`

## YAML Basics (5 minute primer)

YAML is **much easier** than JSON. Key rules:

- **No quotes needed** for most text (only when text contains special characters like `:`)
- **No commas** between items
- **Indentation matters** - use 2 spaces (not tabs)
- **Lists start with `-`**
- **Comments start with `#`**

## Adding a New Event

### Step 1: Copy an existing event

Find an event similar to what you want to add, copy the entire block from `- id:` to the line before the next `- id:`.

### Step 2: Edit the fields

```yaml
- id: evt_008  # Must be unique! Format: evt_XXX
  title_en: Your Event Title in English
  title_es: Tu Título del Evento en Español
  
  # Descriptions: 50-1000 characters, can span multiple lines naturally
  description_en: |
    Write a detailed description of the event in English.
    You can use multiple lines without any special formatting.
    Just keep the text aligned under 'description_en:'.
  description_es: |
    Escribe una descripción detallada del evento en español.
    Puedes usar múltiples líneas sin formato especial.
    Solo mantén el texto alineado bajo 'description_es:'.
  
  # Tags: Pick 2-6 from the controlled vocabulary (see list below)
  tags:
    - contemporary
    - photography
    - political
  
  # Category: One of: gallery, museum, street, pop-up, opening, cultural-center
  category: gallery
  
  # Domain (optional): visual-art, music, theatre, cinema, multi
  domain: visual-art  # Or leave as 'null' or omit entirely
  
  # Dates: Format YYYY-MM-DD or use "unknown"
  start_date: 2025-12-01
  end_date: 2026-01-15
  
  # Venue: Must match an existing venue ID (v_01, v_02, etc.)
  venue_id: v_01
  
  # Cost: free, low, mid, high, unknown
  cost_bucket: mid
  
  # Outdoor: true, false, or "unknown"
  outdoor: false
  
  # Coordinates: Must be in Barcelona (lat: 41.30-41.50, lon: 2.00-2.30)
  latitude: 41.3851
  longitude: 2.1734
  
  # Source: curated (our data) or external (from partners)
  source_type: curated
  
  # Optional fields - use null if not applicable
  accessibility_notes: Wheelchair accessible, audio guide available
  booking_url: https://www.example.com/book
```

## Adding a New Venue

```yaml
- id: v_08  # Must be unique! Format: v_XX
  name: Name of the Venue
  
  # Type: museum, gallery, street-cluster, cultural-center, outdoor-space
  type: museum
  
  neighborhood: El Raval
  
  # Coordinates: Same as events
  latitude: 41.3851
  longitude: 2.1734
  
  # Optional fields
  opening_hours: Tue-Sun 10:00-19:00
  accessibility_notes: Fully accessible
  url: https://www.venue-website.com
```

## Controlled Vocabulary (Tags)

**You must use tags from this list only:**

### Periods/Styles
- modern
- contemporary
- baroque
- renaissance
- surrealism
- abstract
- conceptual
- minimalism

### Media Types
- photography
- painting
- sculpture
- installation
- video
- performance
- digital
- mixed-media

### Themes
- street
- urban
- nature
- portrait
- experimental
- political
- feminist

### Audience
- family-friendly
- educational
- immersive
- interactive

## Common Mistakes to Avoid

### ❌ DON'T DO THIS:
```yaml
# Wrong indentation
- id: evt_008
title_en: No Space Before  # WRONG!

# Missing dash for list
tags:
  modern  # WRONG! Needs a dash

# Using invalid values
cost_bucket: expensive  # WRONG! Not in allowed list
```

### ✅ DO THIS:
```yaml
# Correct indentation
- id: evt_008
  title_en: Two Spaces Before  # CORRECT!

# Dash for list items
tags:
  - modern  # CORRECT!

# Valid cost bucket
cost_bucket: high  # CORRECT!
```

## Tips for Multi-line Descriptions

Use the pipe `|` character for natural multi-line text:

```yaml
description_en: |
  This is the first paragraph of your description.
  You can keep writing naturally.
  
  You can even add paragraph breaks by leaving an empty line.
  
  The validator requires 50-1000 characters total.
```

## Validation Messages

When you run the validator, you'll see:

### ✅ Success:
```
✅ Validation passed! All data is valid.
```

### ❌ Errors with helpful messages:
```
❌ events → 3 → tags: Value error, Tags not in controlled vocabulary: ['invalid_tag']
```

This tells you:
- **Location**: events → 3 (the 4th event, since we count from 0)
- **Field**: tags
- **Problem**: 'invalid_tag' is not in the controlled vocabulary

## Need Help?

Common issues:

1. **"String should have at least 50 characters"**
   - Your description is too short. Add more detail!

2. **"Tags not in controlled vocabulary"**
   - Check the tag list above. Fix any typos.

3. **"References non-existent venue"**
   - Make sure the venue_id matches an existing venue's id field

4. **"start_date must be <= end_date"**
   - Check your dates - the event can't end before it starts!

5. **"Outside Barcelona bounds"**
   - Verify coordinates are correct (use Google Maps to get lat/lon)

## VS Code Tips

If using VS Code:

1. Install the **YAML extension** for syntax highlighting
2. Enable **format on save** to auto-fix indentation
3. You'll see red squiggles for syntax errors as you type

## Quick Reference Card

| Field | Required? | Format | Example |
|-------|-----------|--------|---------|
| id | ✅ | evt_XXX | evt_008 |
| title_en/es | ✅ | 5-200 chars | "Modern Art Exhibition" |
| description_en/es | ✅ | 50-1000 chars | Use \| for multi-line |
| tags | ✅ | 2-6 from list | - contemporary<br>- painting |
| category | ✅ | See list | museum |
| domain | ❌ | visual-art, music, etc | visual-art |
| start/end_date | ✅ | YYYY-MM-DD or "unknown" | 2025-12-01 |
| venue_id | ✅ | v_XX | v_01 |
| cost_bucket | ✅ | free/low/mid/high/unknown | mid |
| outdoor | ✅ | true/false/"unknown" | false |
| lat/lon | ✅ | Barcelona coords | 41.3851, 2.1734 |
| source_type | ✅ | curated/external | curated |
| accessibility_notes | ❌ | Free text | "Wheelchair accessible" |
| booking_url | ❌ | URL or "unknown" | https://... |

---

**Remember**: You can't break anything! The validator will catch all errors before the data is used. Just edit, save, validate, and fix any errors. 🎨
