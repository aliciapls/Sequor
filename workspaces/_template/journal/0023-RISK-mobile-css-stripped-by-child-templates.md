# Risk: Mobile Responsiveness CSS Nesting Bug

## Date: 2026-05-05

## Finding

When adding mobile-responsive CSS to `_portal.html`, the CSS was placed inside `{% block page_style %}` which child templates (`{% extends "_portal.html" %}`) override. This caused the mobile CSS to be silently stripped from rendered pages — the `@media` rules disappeared entirely, leaving only the Jinja2 block tag text visible at the top of the page.

## Root Cause

`{% block page_style %}` in the base template is an override point — child templates like `dashboard.html` redefine it with their own CSS, replacing the base content. Any CSS placed inside that block gets replaced.

## Fix Applied

Mobile CSS moved to a **second, separate `<style>` block** placed after the closing `</style>` tag:

```html
    {% block page_style %}{% endblock %}
</style>
<style>
    /* ── Mobile ── */
    @media (max-width: 768px) { ... }
</style>
{% block extra_head %}{% endblock %}
```

This ensures the mobile CSS is always present regardless of child template overrides.

## Files Changed

- `src/sequor/onboarding/templates/_portal.html` — added hamburger button in topbar, sidebar overlay, mobile @media CSS in separate block, JS toggle function

## Status: RESOLVED

## Prevention

When editing `_portal.html` Jinja2 base templates: CSS that must apply universally (not overridable by child templates) must go in a **separate `<style>` block after `</style>`**, not inside any `{% block %}`.
