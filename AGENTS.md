# DKM working rules

Read PROJECT_CONTEXT.md before editing. Preserve the existing architecture and
verify the actual code before replacing or extending anything.

- Always use a feature branch; never edit or push directly to main.
- Create a pull request whenever changes are pushed. Do not merge without approval.
- Keep existing user changes intact. Do not stage unrelated changes automatically.
- Test payment state transitions and concurrency. Provider confirmation is not
  entitlement; mock payments must never spend tokens or grant access.
- Preserve the KnowledgeAsset deployment and existing buyer entitlements when
  changing Marketplace. Do not treat locally compiled code as deployed code.
- Keep keys and credentials out of commits, tool output and frontend code.
- Follow contracts/AGENTS.md for contract work.
