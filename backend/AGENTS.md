# Backend working instructions

- Keep API endpoints thin; place domain logic in services when those services exist.
- Keep API schemas separate from future persistence models.
- Enforce authorization in the backend for every future private resource.
- Keep deterministic metrics outside the Fitness Agent.
- Never store secrets in source code, examples, tests, or logs.
- Add the smallest applicable unit or integration tests for observable behavior.
- Before finishing, run Ruff checks, mypy, and pytest.
