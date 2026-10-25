# frontend

Next.js 14 / React application. Run `npm ci`, then `npm run dev` here. For production preview use `npm run build` and `npm run start`; rebuild after source changes. The backend normally listens on localhost:8000. The current UI is wallet-only; retained provider components do not imply that fiat checkout is enabled.

## Files

### [.eslintrc.json](.eslintrc.json)

Structured .eslintrc configuration/evidence. Its existence alone is not live-state proof.

### [.gitignore](.gitignore)

Repository/tooling metadata controlling ignores, linting or project behavior; not user-facing application logic.

### [components.json](components.json)

Structured components configuration/evidence. Its existence alone is not live-state proof.

### [next.config.mjs](next.config.mjs)

Build/runtime/tooling configuration for next.config. Review this alongside its package manifest; secrets are deliberately excluded.

### [package-lock.json](package-lock.json)

Dependency lockfile: exact resolved dependency graph and integrity metadata. Used for reproducible installation; not application business logic.

### [package.json](package.json)

Node package manifest: scripts and direct dependencies. Version ranges are not necessarily the versions resolved in the lockfile.

### [postcss.config.mjs](postcss.config.mjs)

Build/runtime/tooling configuration for postcss.config. Review this alongside its package manifest; secrets are deliberately excluded.

### [tailwind.config.ts](tailwind.config.ts)

Build/runtime/tooling configuration for tailwind.config. Review this alongside its package manifest; secrets are deliberately excluded.

### [tsconfig.json](tsconfig.json)

Structured tsconfig configuration/evidence. Its existence alone is not live-state proof.

## Subdirectories

- [app](app/README.md)
- [lib](lib/README.md)
- [providers](providers/README.md)
- [tests](tests/README.md)
