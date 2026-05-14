# Session: Settings Page CSS Rewrite — 2026-05-14

## What Happened

Thorough CSS refactor of the `/portal/settings` page to fix spacing and alignment issues.

## Root Cause

The original settings page used `h3` elements for section headers inside `.card` (which has no built-in padding/body). The body's `line-height: 1.6` combined with h3 font metrics created uneven, unpredictable vertical spacing that no amount of padding/margin tweaking could make consistent.

## Key Changes

### Pattern: div-based section headers instead of h3

**Before:** `h3` with `padding-bottom`, `margin`, and `border-bottom` — all fighting each other
**After:** `div.settings-section-header` with only `margin-bottom`, separated from `div.settings-section` padding

```html
<!-- Before: h3 fighting with section margins -->
<div class="settings-section">
  <h3 style="padding-bottom, margin fighting spacing">Account</h3>
  <div class="settings-row">...</div>
</div>

<!-- After: section provides padding, header is only a label -->
<div class="settings-section" style="padding: 14px 22px">
  <div class="settings-section-header" style="margin-bottom: 8px">Account</div>
  <div class="settings-row" style="padding: 11px 0">...</div>
</div>
```

### Pattern: section padding drives horizontal space, row padding drives vertical

- `.settings-section { padding: 14px 22px }` — all horizontal padding from section
- `.settings-row { padding: 11px 0 }` — only vertical padding in rows
- `.settings-section + .settings-section { border-top: 1px solid var(--slate-100) }` — section separation

### Key CSS decisions

| Element                    | Padding                      | Why                                            |
| -------------------------- | ---------------------------- | ---------------------------------------------- |
| `.settings-section`        | `padding: 14px 22px`         | Provides horizontal padding for all content    |
| `.settings-section-header` | `margin-bottom: 8px`         | Small gap between label and first row          |
| `.settings-row`            | `padding: 11px 0`            | Vertical padding only; horizontal from section |
| Section sibling border     | `border-top` on `+` adjacent | Clean separation between sections              |

## Other Pages Fixed Today

- **Login page**: Added show/hide password toggle with clean event listener
- **Signup page**: Fixed footer text wrapping with `white-space: nowrap`
- **Sidebar**: Removed click handler from user info area, fixed email display (was overwriting with account_name)

## Commits Pushed

- `8f746ed` fix: improve settings page padding for better readability
- `a77a793` fix: prevent footer text wrapping on signup page
- `04f2f27` feat: add show password toggle to login page
- `c3a95cb` fix: rewrite settings page CSS for clean, consistent spacing
- `50b785a` fix: unify settings page row spacing with first-of-type border
- `956205c` fix: tighten h3 spacing with line-height:1 and explicit padding-top
- `8747803` fix: use div instead of h3 for section labels
- `4d6394f` fix: match subscription page card-body spacing pattern
- `c04d32d` fix: simplify settings CSS using section padding + sibling border

## Files Changed

- `src/sequor/onboarding/templates/settings.html` — CSS rewrite, h3 → div
- `src/sequor/onboarding/templates/login.html` — show password toggle
- `src/sequor/onboarding/templates/register.html` — footer nowrap
- `src/sequor/onboarding/templates/_portal.html` — sidebar user info fix
