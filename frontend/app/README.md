# frontend/app

App Router pages. Public entry is welcome followed by signup/login; AppShell and backend authorization protect application workflows. Each page directory has a README describing its route.

## Files

### [favicon.ico](favicon.ico)

Static visual/font asset, consumed by frontend rendering; no executable business logic.

### [globals.css](globals.css)

Shared style definitions and visual tokens for the application.

### [layout.tsx](layout.tsx)

Root Next.js layout, global styling and providers; wraps page rendering.

Main entry points: `RootLayout`.

### [page.tsx](page.tsx)

Unauthenticated welcome entry point; app functions become available after authentication.

Main entry points: `Home`.

## Subdirectories

- [account](account/README.md)
- [auctions](auctions/README.md)
- [backend-test](backend-test/README.md)
- [dashboard](dashboard/README.md)
- [fonts](fonts/README.md)
- [funding](funding/README.md)
- [login](login/README.md)
- [marketplace](marketplace/README.md)
- [mint](mint/README.md)
- [research](research/README.md)
- [search](search/README.md)
- [signup](signup/README.md)
- [status](status/README.md)
