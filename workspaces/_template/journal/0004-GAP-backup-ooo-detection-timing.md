# GAP: Backup OOO detection timing is unspecified

**Type:** GAP
**Date:** 2026-04-19

## Finding

The specs say "if backup is also OOO, route to second-tier immediately" but don't specify WHEN the system checks whether the backup is OOO.

Three options:

1. **At configuration time**: when primary configures their OOO, system checks if backup is also OOO during that window → warns primary
2. **At escalation time**: every escalation checks if backup is currently OOO → routes to second-tier dynamically
3. **Continuously**: system monitors both primary and backup OOO status and pre-routes escalations before they happen

## Implication

If backup goes OOO mid-period (after primary already left), the current spec has no defined behavior. The primary is unreachable and can't reconfigure. Contacts' messages get routed to a backup who is also absent.

## Action Required

Define backup OOO detection timing as an ADR before build. Recommended: continuous monitoring with dynamic re-routing. This is architecturally simple (check OOOConfiguration table at escalation time) and handles the mid-period change case.
