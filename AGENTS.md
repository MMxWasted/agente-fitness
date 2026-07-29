# AGENTS.md

## Project

Agente Fitness is a mobile-first fitness tracking, analytics and coaching application.

Its purpose is to let users record workouts, routines, exercises, body measurements, nutrition data and fitness goals. The application will calculate objective metrics and will later include an AI agent that can explain those metrics and generate controlled recommendations.

Codex is the development agent used to build and maintain the repository. The Fitness Agent is a feature inside the final application. Do not confuse both roles.

The project is currently in its planning stage. Do not claim that a feature exists unless it is present and verified in the repository.

## Source of truth

Before starting a task, inspect the relevant files.

The main project documents are:

* `README.md`
* `AGENTS.md`
* `docs/PLAN_MAESTRO.md`
* `docs/product/`
* `docs/architecture/`
* `docs/decisions/`
* `docs/development/`
* `docs/safety/`

When documentation and implementation disagree, report the inconsistency. Do not silently assume which one is correct.

## Intended repository structure

The repository is expected to contain:

* `frontend/`: React and TypeScript application.
* `backend/`: FastAPI application, deterministic analytics and Fitness Agent.
* `docs/`: product, architecture, decisions, development and safety documentation.
* `scripts/`: reproducible maintenance and seed scripts.
* `.github/`: continuous integration and repository templates.

Do not create this entire structure unless the current task explicitly requires it.

## General working rules

1. Read the relevant documentation before modifying code.
2. Inspect the existing implementation before proposing changes.
3. For non-trivial tasks, present a short implementation plan before editing.
4. Keep every task focused on its stated objective.
5. Do not implement unrelated features.
6. Do not perform speculative refactors.
7. Do not add abstractions without a concrete current use case.
8. Do not add production dependencies without explaining why they are necessary.
9. Prefer established project patterns over introducing new patterns.
10. Preserve backward compatibility unless the task explicitly authorizes breaking changes.
11. Update documentation when observable behavior changes.
12. Do not claim completion without verification evidence.
13. Review the final diff before finishing.
14. Report unresolved risks, limitations and failed checks.
15. Never hide failing tests or validation errors.

## Planning-only tasks

When a task explicitly requests analysis or planning only:

* Do not create files.
* Do not modify files.
* Do not delete files.
* Do not rename files.
* Do not install dependencies.
* Do not run migrations.
* Do not implement code.
* Do not create commits.
* Do not continue into implementation without a separate instruction.

You may inspect files and Git status when permitted.

## Architecture rules

The intended architecture uses:

* React with TypeScript for the frontend.
* FastAPI for the backend.
* PostgreSQL for persistence.
* SQLAlchemy for data access.
* Alembic for migrations.
* Pydantic for request, response and agent schemas.
* Deterministic domain services for calculations.
* OpenAI Agents SDK for the Fitness Agent.
* Docker Compose for local infrastructure.
* GitHub Actions for continuous integration.

These technologies are planned, not automatically approved for every task. Do not initialize or install them unless required by the current phase.

## Backend architecture

Backend code should be separated into clear responsibilities:

* API routes.
* Request and response schemas.
* Domain services.
* Repositories.
* Persistence models.
* Database configuration.
* Authentication and authorization.
* Deterministic analytics.
* Routine generation rules.
* Agent tools.
* Agent guardrails.
* Agent output models.

API route handlers should remain thin.

Do not place complex domain calculations directly inside route handlers.

Do not access the database directly from the Fitness Agent.

Do not place OpenAI API calls inside unrelated domain services.

## Frontend architecture

Frontend code should be organized by feature.

Expected feature areas include:

* Authentication.
* Profile.
* Goals.
* Exercises.
* Routines.
* Workouts.
* Measurements.
* Nutrition.
* Analytics.
* Fitness Agent.

The frontend must:

* Use TypeScript.
* Validate user input.
* Handle loading states.
* Handle empty states.
* Handle error states.
* Be designed mobile-first.
* Avoid storing secrets.
* Never expose the OpenAI API key.
* Use the backend API instead of directly accessing external AI services.

## Data and domain rules

1. A user may only access their own private data.
2. Authorization must be enforced in the backend.
3. Client-provided ownership identifiers must not be trusted.
4. Historical workout data must remain stable when routines are edited.
5. Only one routine may be active per user unless an ADR changes this rule.
6. Global exercises must not be editable by normal users.
7. Custom exercises must belong to their creator.
8. Destructive actions must be explicit.
9. Important multi-step operations should use database transactions.
10. Dates and weekly aggregations must respect the user's timezone.
11. Database schema changes require Alembic migrations.
12. Migrations must be reversible when reasonably possible.
13. Seed data must be reproducible.
14. Do not commit generated databases or local data files.

## Deterministic analytics rules

Important fitness metrics must be calculated in deterministic code.

Examples include:

* Training volume.
* Weekly sets.
* Muscle-group frequency.
* Workout adherence.
* Personal records.
* Weight trends.
* Moving averages.
* Measurement changes.
* Exercise progression.
* Period comparisons.
* Estimated one-repetition maximum.
* Nutrition averages.

Every important calculation must:

* Have a documented definition.
* State its assumptions.
* Handle missing data.
* Have unit tests with known inputs and expected outputs.
* Avoid relying on a language model.

The model may explain a metric, but it must not invent or independently calculate stored metrics when a deterministic service is available.

## Fitness Agent rules

The initial architecture must use one orchestrating Fitness Agent unless a documented ADR authorizes additional agents.

The Fitness Agent:

* Must access user information only through approved tools.
* Must not receive direct SQL access.
* Must not select an arbitrary user identifier.
* Must use the authenticated user context.
* Must return validated structured output when required.
* Must identify missing information.
* Must distinguish facts from suggestions.
* Must include evidence for data-based observations.
* Must not invent measurements or workout records.
* Must not expose private chain-of-thought.
* Must provide concise explanations instead of internal reasoning.
* Must handle tool failures.
* Must handle model timeouts.
* Must not modify important data without explicit confirmation.
* Must be testable without making real OpenAI calls.

Tests should use mocks or fake model clients by default.

Live-model evaluations must be optional and separated from the normal test suite.

## Confirmation rules

The Fitness Agent must require explicit user confirmation before:

* Activating a routine.
* Replacing an active routine.
* Modifying a fitness goal.
* Modifying planned loads.
* Editing historical workouts.
* Deleting records.
* Saving new limitations.
* Persisting important nutrition changes.
* Exporting data.
* Sharing data.
* Deleting an account.

A recommendation may be saved as a proposal without applying the underlying action.

## Health and safety rules

The application is not a medical device.

The Fitness Agent must not:

* Diagnose injuries.
* Diagnose diseases.
* Prescribe medication.
* Provide emergency medical treatment.
* Replace a doctor, physiotherapist or registered dietitian.
* Recommend ignoring acute or severe symptoms.
* Guarantee physical results.

Potentially serious symptoms include:

* Chest pain.
* Difficulty breathing.
* Fainting.
* Loss of consciousness.
* Severe or acute pain.
* Heavy bleeding.
* Neurological symptoms.
* Serious injury.
* Extreme eating behavior.
* Dangerous substance use.

When these situations are detected, the agent should stop normal coaching behavior, explain its limitations and recommend appropriate professional help.

Health and safety behavior must be covered by dedicated evaluations.

## Privacy and security rules

1. Never commit API keys, passwords, tokens or secrets.
2. Use environment variables for configuration.
3. Maintain an accurate `.env.example` without real values.
4. Never place the OpenAI API key in frontend code.
5. Passwords must use a secure password-hashing algorithm.
6. Authentication tokens must have a documented expiration strategy.
7. Sensitive information must not be unnecessarily included in logs.
8. Do not log complete prompts or tool responses containing personal data unless explicitly justified.
9. Apply least-privilege access.
10. Validate all input on the backend.
11. Do not trust frontend validation as a security control.
12. Protect endpoints against access to another user's resources.
13. Add rate limiting where appropriate.
14. Data export and account deletion must be documented and tested.
15. Security-sensitive decisions require an ADR or security document update.

## Documentation rules

Update the relevant documentation when changing:

* Product behavior.
* Architecture.
* Database entities.
* API contracts.
* Authentication.
* Authorization.
* Agent tools.
* Agent output schemas.
* Guardrails.
* Environment variables.
* Development commands.
* Deployment.
* Testing strategy.

Do not document future functionality as already implemented.

Mark planned, partial and completed functionality accurately.

Use Mermaid diagrams when they improve understanding, but keep written explanations as the primary source of truth.

## Dependency rules

Before adding a dependency:

1. Explain the problem it solves.
2. Check whether the existing stack already solves the problem.
3. Prefer maintained and widely used packages.
4. Consider security and licensing.
5. Avoid overlapping libraries.
6. Add the dependency through the repository's package manager.
7. Update lock files.
8. Update setup documentation when necessary.
9. Run the relevant tests and build.

Do not manually edit lock files.

## Testing rules

Use the smallest appropriate test level:

* Unit tests for domain calculations.
* Integration tests for database and API behavior.
* Component tests for frontend behavior.
* End-to-end tests for critical user flows.
* Agent evaluations for tool selection, factual grounding and guardrails.

Tests must cover relevant error cases.

Important authorization tests should include attempts to access another user's data.

Important analytics tests should use known datasets and expected results.

The standard test suite must not depend on:

* A live OpenAI call.
* A developer's personal database.
* Uncommitted secrets.
* External services that are not explicitly mocked.

## Command rules

Use only commands that exist in the repository.

Do not invent commands because they appear in this document or in the project plan.

Before running a command:

* Check the relevant package configuration.
* Check the README.
* Check available scripts.
* Use the repository's selected package manager.

When the backend is initialized, expected commands may include:

```text
uv sync
uv run uvicorn app.main:app --reload
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy app
```

When the frontend is initialized, expected commands may include:

```text
npm install
npm run dev
npm run test
npm run lint
npm run typecheck
npm run build
```

These commands are examples until the corresponding configuration exists.

If a command cannot run:

* Report the exact command.
* Report the relevant error.
* Do not claim that the check passed.
* Do not silently skip required verification.

## Git rules

1. Inspect `git status` before starting when Git access is available.
2. Do not discard user changes.
3. Do not overwrite unrelated modifications.
4. Keep changes focused.
5. Do not rewrite Git history unless explicitly requested.
6. Do not force-push.
7. Do not commit secrets.
8. Do not create a commit unless explicitly requested.
9. Review the diff before finishing.
10. Mention uncommitted or pre-existing changes in the final report.

Recommended branch names:

* `feature/name`
* `fix/name`
* `docs/name`
* `refactor/name`
* `test/name`
* `chore/name`

Recommended commit prefixes:

* `feat`
* `fix`
* `docs`
* `test`
* `refactor`
* `chore`

## Definition of done

A task is complete only when all applicable conditions are satisfied:

* Acceptance criteria are met.
* The implementation matches the documented architecture.
* Input validation exists.
* Authorization is enforced.
* Relevant tests exist.
* Tests pass.
* Linting passes.
* Type checking passes.
* The build passes when applicable.
* Database migrations are included when necessary.
* Documentation is updated.
* No secrets are committed.
* No unrelated changes are included.
* Mobile behavior is considered for frontend work.
* Error and loading states are implemented when relevant.
* Historical data remains consistent.
* The final diff has been reviewed.
* Remaining risks are clearly reported.

## Required final response

At the end of an implementation task, provide:

1. A concise summary.
2. Files created.
3. Files modified.
4. Important implementation decisions.
5. Database migrations added.
6. Tests added or updated.
7. Exact verification commands executed.
8. Results of each verification command.
9. Unresolved risks or limitations.
10. Recommended next step.

Do not claim that a task is complete when required checks fail.

For planning-only tasks, provide:

1. Repository observations.
2. Assumptions.
3. Proposed plan.
4. Files that would be affected.
5. Risks.
6. Verification criteria.

Do not implement anything during a planning-only task.
