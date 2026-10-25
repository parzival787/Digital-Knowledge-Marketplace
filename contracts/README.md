# contracts

Active Solidity project using Hardhat 3 with the Mocha/ethers toolbox and OpenZeppelin. Run `npm ci`, `npx hardhat test` and `npx tsc --noEmit` here. Source compiler is 0.8.37. Deployment scripts send public transactions: do not execute them as startup or test commands. The successor preserves legacy registrations 1-6; new registrations start at 7. Marketplace purchases grant access without transferring the registration NFT. See `cents-deployment.json` for the recorded current deployment and read AGENTS.md before contract changes.

## Files

### [.gitignore](.gitignore)

Repository/tooling metadata controlling ignores, linting or project behavior; not user-facing application logic.

### [AGENTS.md](AGENTS.md)

Developer/agent workflow instructions and tooling guidance; not executed as an application feature.

### [CLAUDE.md](CLAUDE.md)

Developer/agent workflow instructions and tooling guidance; not executed as an application feature.

### [cents-deployment.json](cents-deployment.json)

Current Amoy successor deployment receipts, original-state snapshot and wiring verification.

### [deployment.json](deployment.json)

Earlier deployment record; compare with the current cents manifest before using addresses.

### [hardhat.compiler-review.config.ts](hardhat.compiler-review.config.ts)

Build/runtime/tooling configuration for hardhat.compiler-review.config. Review this alongside its package manifest; secrets are deliberately excluded.

### [hardhat.config.ts](hardhat.config.ts)

Build/runtime/tooling configuration for hardhat.config. Review this alongside its package manifest; secrets are deliberately excluded.

### [package-lock.json](package-lock.json)

Dependency lockfile: exact resolved dependency graph and integrity metadata. Used for reproducible installation; not application business logic.

### [package.json](package.json)

Node package manifest: scripts and direct dependencies. Version ranges are not necessarily the versions resolved in the lockfile.

### [pnpm-lock.yaml](pnpm-lock.yaml)

Dependency lockfile: exact resolved dependency graph and integrity metadata. Used for reproducible installation; not application business logic.

### [pnpm-workspace.yaml](pnpm-workspace.yaml)

Build/runtime/tooling configuration for pnpm-workspace. Review this alongside its package manifest; secrets are deliberately excluded.

### [tsconfig.json](tsconfig.json)

Structured tsconfig configuration/evidence. Its existence alone is not live-state proof.

## Subdirectories

- [contracts](contracts/README.md)
- [scripts](scripts/README.md)
- [test](test/README.md)
