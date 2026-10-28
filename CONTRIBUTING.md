# Contributing

1. Fork, then create a branch from `main`.
2. `make install` and copy `.env.example` to `.env`.
3. Make your change with tests. Pure astrology logic lives in `vedic_astro/core` and must stay free of Flask imports.
4. `make format && make lint && make test` must pass (coverage gate: 85%).
5. Open a pull request describing the behaviour change. For astrology rules, cite the classical or reference source you followed.

