# frontend/components/layout

Part of DKM. See the root README for startup, trust boundaries and validation.

## Files

### [AppShell.tsx](AppShell.tsx)

Session-aware navigation gate: welcome/login/signup before authentication; dashboard/workspace after authentication. Backend remains the actual authorization boundary.

Main entry points: `AppShell`.

### [Navbar.tsx](Navbar.tsx)

Authenticated application navigation.

Main entry points: `Navbar`.
