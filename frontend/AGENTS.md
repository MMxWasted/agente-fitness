# Frontend working instructions

- Keep TypeScript in strict mode and preserve the feature-oriented structure.
- Build accessible, mobile-first components with explicit loading and error states.
- Communicate with the backend through modules in `src/services`; components must not hardcode API URLs.
- Never store secrets or backend credentials in frontend code or environment examples.
- Test observable user behavior without depending on live external services.
- Do not introduce dependencies without a current, documented need.
- Before finishing, run `npm run lint`, `npm run typecheck`, `npm run test`, and `npm run build`.
