---
name: vue-optimize
description: Analyze Vue 3 component structure and suggest optimizations for performance and code reuse. Use when asked to review, audit, optimize, or refactor .vue components in client/src for performance, reactivity, or duplication — or when a component feels too large or slow.
---

# Vue Component Optimization Analysis

This skill audits Vue 3 (Composition API) components in `client/src/` and produces a
prioritized list of performance and code-reuse improvements. It is an **analysis** skill:
it inspects code and reports findings. When the user approves a change, apply `.vue`
edits by delegating to the **vue-expert** subagent (per the project rule: any create or
significant modification of a `.vue` file goes through vue-expert).

## Scope

- **Views**: `client/src/views/*.vue` (page-level, often large — Dashboard.vue is ~1270 lines)
- **Components**: `client/src/components/*.vue` (reusable UI, mostly modals + FilterBar)
- **Composables**: `client/src/composables/*.js` (`useFilters`, `useAuth`, `useI18n`)

Ground every suggestion in the conventions documented in `client/CLAUDE.md` — do not invent
new patterns. This project uses: Composition API only, refs for raw state + computed for
derived data, shared state via composables, custom SVG charts, and scoped styles.

## Workflow

1. **Select targets.** If the user names components, analyze those. Otherwise sweep
   `client/src/views/` and `client/src/components/`, and prioritize the largest files
   (`wc -l client/src/views/*.vue client/src/components/*.vue`) — size is the strongest
   signal for both perf and reuse issues here.
2. **Read each target** plus the composables, so you can tell "should be extracted" from
   "already extracted elsewhere."
3. **Run the checklists below** against each file.
4. **Report** findings ranked by impact (see Output Format). Do not edit yet.
5. **On approval**, delegate the edits to vue-expert with a precise change list, then
   suggest verifying with the Playwright MCP tools against `http://localhost:3000`.

## Performance Checklist

Check each component for:

- **Work in methods that should be computed.** Filtering/mapping/reducing called from the
  template (e.g. `getBacklogByPriority('high')` invoked 3× in Backlog.vue) re-runs on every
  render. Move to a `computed` (cached until deps change) or precompute a keyed map.
  *Reference: client/CLAUDE.md "Computed vs Methods".*
- **Repeated derivations in the template.** The same `filter`/`reduce` expression appearing
  multiple times → hoist into one computed.
- **`v-if` on frequently toggled content.** For charts/panels toggled often, prefer `v-show`.
  Keep `v-if` for rarely shown content. *Reference: "v-show vs v-if".*
- **Array index as `:key`.** `:key="index"` in `v-for` causes incorrect DOM reuse — flag and
  replace with a stable id (`sku`, `id`, `month`, `order_number`).
- **Unvalidated date parsing.** `new Date(x).getMonth()` without an `isNaN(date.getTime())`
  guard — a known project pitfall.
- **Undebounced watchers driving API calls / expensive work.** Search-box or resize watchers
  that fire per keystroke → debounce (`watchDebounced` from `@vueuse/core`).
- **Large inline chart/data transforms in the template.** SVG chart math belongs in computed
  properties, not recomputed inline each render.
- **Reactivity foot-guns.** Destructured props in `setup` (loses reactivity), mutated props,
  or missing `.value` in script.
- **Heavy always-mounted views** that could use `defineAsyncComponent` for code splitting.

## Code Reuse Checklist

Check across components for:

- **Duplicated loading/error/data-fetch scaffolding.** The `loading`/`error` refs +
  `try/catch/finally` + `watch(filters, load)` block is copied across nearly every view.
  Candidate for a `useResource(fetchFn)` composable.
- **Duplicated formatting logic.** Currency / large-number / percentage / date formatting
  repeated inline → extract a `useFormatters` composable or shared util.
- **Repeated filter wiring.** Components re-implementing filter-to-query-param logic that
  `useFilters` (`getCurrentFilters`) already provides.
- **Copy-pasted template blocks.** Repeated stat cards, table shells, badges, or modal
  chrome across files → extract a small reusable component in `client/src/components/`.
- **Oversized components.** Per client/CLAUDE.md thresholds: template >100 lines or logic
  >150 lines → recommend splitting (call out Dashboard.vue specifically).
- **Logic that belongs in a composable.** State shared across components, or a reusable
  logic pattern implemented locally in one view.

Before recommending an extraction, confirm the shared code does NOT already exist in
`client/src/composables/` — recommend using the existing composable instead of a new one.

## Output Format

Report as a ranked list. For each finding:

```
### <ComponentName.vue> — <short title>
- **Type:** Performance | Reuse
- **Impact:** High | Medium | Low
- **Location:** file:line
- **Issue:** what's wrong and why it costs performance / causes duplication
- **Suggested fix:** concrete change, referencing the client/CLAUDE.md pattern to follow
- **Effort:** small | medium | large
```

End with a short summary: top 3 highest-impact changes and any cross-cutting extraction
(e.g. a proposed composable) that would remove duplication in multiple files at once.

## Applying Fixes

Only after the user approves specific findings:

1. Delegate each `.vue` change to **vue-expert** with the exact file, line, and intended edit.
2. Keep behavior identical unless the user asked otherwise — optimizations should not change
   what the UI renders.
3. Suggest verification: run the app (`start` skill) and drive the affected view with the
   Playwright MCP tools at `http://localhost:3000`; run frontend tests via the `test` skill.
