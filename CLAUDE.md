# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django 5.2.8 project for managing job applicants with screening questions and geolocation features. The project uses PostgreSQL with PostGIS extensions for geospatial queries. The main application is the `appliers` app which handles applicants, users, and screening questions.

## Database Setup

The project uses PostgreSQL with PostGIS extensions. Two database options are available:

1. **PostgreSQL via Docker** (recommended for local development):
   ```bash
   docker-compose up -d
   ```
   Connection string: `postgres://postgres:admin@localhost:5432/interview`

2. **SQLite** (alternative):
   Configure in `laenk/settings.py` via the `DATABASE_URL` environment variable.

After setting up the database, run migrations:
```bash
python manage.py migrate
```

## Development Setup

1. Create and activate virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Populate database with test data (1.22M records: 70k users, 150k appliers, 1M questions):
   ```bash
   python manage.py populate_db
   ```
   Note: This takes several minutes to complete.

4. Run development server:
   ```bash
   python manage.py runserver
   ```

## Running Tests

```bash
python manage.py test
```

To run a specific test case:
```bash
python manage.py test appliers.tests.SearchViewSetTestCase
```

To run a single test method:
```bash
python manage.py test appliers.tests.SearchViewSetTestCase.test_search_without_qualified_filter
```

## Architecture

### Models (appliers/models.py)

Three main models with a timestamp mixin:

1. **User**: Represents applicants with personal information (name, email, phone, resume, cover letter, country)
2. **Applier**: Job applications linked to users, includes:
   - `qualified` status (YES/NO/PENDING)
   - `source` (JSONField for tracking application source)
   - Geographic coordinates (`latitude`, `longitude`) for geolocation queries
3. **ScreeningQuestion**: Questions associated with each application (question text, type, answer, skip status)

Relationships:
- User → Applier: One-to-many (one user can have multiple applications)
- Applier → ScreeningQuestion: One-to-many via `screening_questions` related name

### URL Structure

- `/admin/` - Django admin interface
- `/api/v1/appliers/list/` - Applier1ViewSet (slow endpoint with N+1 query problem)
- `/api/v1/appliers/list2/` - Applier2ViewSet (optimized endpoint using subquery)
- `/api/search` - SearchViewSet (geolocation search with optional qualified filter)

### Views

**appliers/views/applier1.py**: Original implementation that fetches appliers with >16 screening questions. Has N+1 query issue due to iterating over queryset and accessing `applier.user` for each record.

**appliers/views/applier2.py**: Optimized version that avoids expensive post-join/aggregate HAVING clause by performing a subquery first to find applier IDs, then fetching those appliers.

**appliers/views/search.py**: Geolocation search endpoint that:
- Accepts `lat`, `lon` query parameters (required)
- Optional `qualified` filter (YES/NO/PENDING, case-insensitive)
- Optional `radius` parameter (default 20km)
- Returns appliers within radius, sorted by distance
- Uses PostGIS for distance calculations

### Performance Considerations

The project is designed to test query optimization strategies:
- Applier1ViewSet demonstrates the N+1 query problem
- Applier2ViewSet shows how to optimize with subqueries
- Both endpoints fetch appliers with >16 screening questions from a large dataset

When working with views, always use `select_related()` for foreign keys and `prefetch_related()` for reverse foreign keys to avoid N+1 queries.

## Key Files

- `laenk/settings.py` - Uses `dj_database_url` for database configuration
- `laenk/urls.py` - Main URL routing, includes API v1 routes
- `appliers/models.py` - Data models with TimeStampedModel base class
- `appliers/management/commands/populate_db.py` - Generates test data in batches
- `docker-compose.yml` - PostGIS database container configuration
