# Changelog

## 1.0.0

### Fixed
- AI chat crashed on every request: the code used the removed `openai.ChatCompletion` API with `openai>=1.0`. Now uses the v1 client.
- `requirements.txt` was missing Flask, pyswisseph and python-dotenv.
- Ascendant, houses and Rahu/Ketu were tropical while planets were sidereal; everything is now Lahiri sidereal.
- Yoni table had the wrong animals for the last nine nakshatras.
- Bhakoot, Nadi, Tara and Graha Maitri now follow the traditional rules (Vashya and Yoni remain simplified).
- Panchanga Yoga and Karana were placeholders; now real names.
- Manglik and house placements are computed from the Lagna (whole-sign houses).
- Chat suggestions were never personalised and were returned in random order.

### Changed
- Restructured into the `vedic_astro` package (core / services / web) with an app factory.
- Chart context lives server-side (memory or Redis); the cookie only carries an opaque id.
- Matching accepts optional birth time (`boy_hour`, `girl_hour`, ...); defaults to noon.
- `/predictions/<path>` placeholder replaced by `/predictions`.

### Added
- Input validation, structured logging, request IDs, security headers, rate limiting, `/health`.
- Pytest suite (~98% coverage), ruff, GitHub Actions CI, Docker, docker-compose with Redis.
