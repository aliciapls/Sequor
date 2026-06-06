# Red-Team Findings — The ANALYSIS Layer (`01-analysis/02`–`09`)

> Scope: the seven product-analysis documents — `02-value-propositions.md`,
> `03-unique-selling-points.md`, `04-platform-model.md`, `05-aaa-framework.md`,
> `06-network-effects.md`, `07-transparency-intervention-architecture.md`,
> `09-risks-failure-points.md` — read against `briefs/01-vision.md`, the research stream
> (`01-research/07`, `08`, `09` esp.), and the shipped/target specs.
>
> Method: first-principles adversarial read. Each finding carries ID · SEVERITY · LOCATION ·
> WHAT'S WRONG · WHY IT MATTERS · FIX. A genuine GAP is distinguished from a stylistic nit.
> Honesty already present in the docs is NOT re-flagged (and §"Credit where due" lists it).
>
> Headline: the analysis is unusually disciplined on its core strategic claims — the four
> load-bearing claims the prompt asked me to verify (M1-leads-the-story / M2-ships-first /
> within-org-then-cross-org / lead-with-Augment) are **internally consistent across docs**,
> and the agent-comms hypothesis is treated as a BET nearly everywhere it appears. BUT there
> is one BLOCKING framework collision (the "AAA" name means two different things in two docs),
> several HIGH overclaims around "80% exists" and the Cowork threat's depth, and a recurring
> understatement of how net-new the genuinely-hard 5% is.

---

## CROSS-DOC CONSISTENCY VERDICT ON THE FOUR CORE CLAIMS (as the prompt required)

| Core claim                    | Verdict                     | Evidence                                                                                                                                                                                                                                                                                                                                    |
| ----------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **M1 leads the story**        | ✅ CONSISTENT               | `03` §8.1 "Lead with M1 … as the headline USP"; `07` whole-doc treats M1+M2 as the signature; `09` §2 ranks M1 the lead moat. Research `07` §11 names M1 the "Lead USP." Coherent.                                                                                                                                                          |
| **M2 ships first**            | ✅ CONSISTENT               | `03` §8.1 "ship M2 … FIRST as the credibility-and-revenue foundation"; `07` §7.1 priority order builds L1/L2 before L3; `09` §5.3 "lead with M2." Coherent.                                                                                                                                                                                 |
| **Within-org then cross-org** | ✅ CONSISTENT               | `04` §6.3 + §6 recommended sequence (intra-org first); `06` §8.1 two-stage ignition (within-org PERSONALIZATION+ENGAGEMENT first, cross-org M4 second). Coherent.                                                                                                                                                                           |
| **Lead with Augment**         | ⚠️ CONSISTENT-BUT-AMBIGUOUS | `05` §5.1 "Lead the wedge with AUGMENT." This does NOT contradict "lead with M1" because `05`'s Augment ≈ M1+M2 (transparency+intervention+posture), explicitly stated `05` §2.1/§4. BUT the dual use of "lead" (lead the _USP story_ with M1 vs lead the _value-axis wedge_ with Augment) is never reconciled in one place — see **F-A2**. |

**The platform-model "primary transaction" (B, the artifact, `04` §2.2) and the network-effects
"primary flywheel" (M4 cross-org artifact exchange, `06` §8.1) DO cohere** — both are M4, both
are sequenced second behind a within-org loop. No contradiction. Good.

**BUT the "lead USP" (M1, `03`) and the "primary network-effects engine / primary transaction"
(M4, `04`+`06`) are different moats playing different roles, and no single doc states the
relationship crisply for a reader who reads only two of the seven.** See **F-A1** (MEDIUM).

---

## BLOCKING

### B-1 — "AAA" names two mutually-inconsistent frameworks across docs 02 and 05, with a broken cross-reference

- **SEVERITY: BLOCKING**
- **LOCATION:** `02-value-propositions.md` §1 lines 104–109 + the inline `AAA lens` tags in §1.1–1.5; vs `05-aaa-framework.md` title + Part 0 (lines 1–23). Plus the cross-ref at `02` lines 23 and 109.
- **WHAT'S WRONG:** Doc 02 defines AAA as **Augment / Automate / Avoid** ("the three cost levers are **Augment** … **Automate** … **Avoid**", line 106–108) and uses those three tags as a costing lens throughout §1. Doc 05 — the dedicated framework doc — defines AAA as **Automate / Augment / Amplify** (title; "Automate removes the hands, Augment sharpens the head, Amplify clones the expert," line 23). The **third axis is different** (Avoid vs Amplify) and they are genuinely different concepts: "Avoid" = eliminate cost categories (licences, integration projects); "Amplify" = scale scarce expertise across orgs. Worse, doc 02 tells the reader twice (lines 23, 109) that "Full definitions live in `03-aaa-framework.md`" — but (a) the framework doc is **`05`-aaa-framework.md**, not `03` (which is `03-unique-selling-points.md`), and (b) even if the filename were right, the definitions there do NOT match the three letters doc 02 just used.
- **WHY IT MATTERS:** AAA is a value-articulation spine cited as a "lens" in the buyer-facing value-props doc and as a standalone framework in doc 05. A buyer or builder who reads doc 02, follows the pointer to "the AAA doc," and finds a _different_ third axis will conclude the analysis does not know its own framework. This is the single most embarrassing inconsistency for a strategy artifact: the named, capitalized, repeatedly-used core acronym resolves to two different things. It is BLOCKING because it cannot be waved off as style — it is a factual contradiction in a load-bearing definition, plus a dead cross-reference.
- **FIX:** Pick ONE AAA. Recommendation: adopt doc 05's **Automate / Augment / Amplify** as canonical (it is the dedicated, fuller, mechanism-grounded treatment and "Amplify" maps cleanly to the M4 network-effects engine, giving AAA→M-moat coherence). Then: (1) rewrite doc 02 §1's lens to Augment/Automate/**Amplify** and re-tag §1.1–1.5 (the "Avoid" cost-elimination idea is real and good — keep it, but as a sub-point under Amplify/Automate, not a third A); (2) fix both cross-references in doc 02 to point to `05-aaa-framework.md`; (3) add a one-line "AAA is defined in 05; this doc uses it as a lens" so the relationship is explicit. If instead the team prefers Augment/Automate/**Avoid**, then doc 05 must be retitled and rewritten — but that loses the Amplify↔M4 mapping, so 05's version is the better keep.

---

## HIGH

### H-1 — "80% already exists" is repeated as a near-headline across 4 docs; the caveat is present but the framing still over-reassures

- **SEVERITY: HIGH**
- **LOCATION:** `08-product-focus-80-15-5.md` §0 ("roughly 80% of this platform's core already exists"), §2 table, §8; `07-transparency…` §0 ("roughly 80% of the substrate … already exists"); `05` Part 1.2/3.2 ("largely ready," "literally already built"); `04` §0/§7.3 ("80% of the exchange layer exists in production").
- **WHAT'S WRONG:** The "80% exists" claim is true _at the level of primitives_ and every doc says so somewhere (doc 08 §0 even calls this "The single most important caveat"). The problem is **proportion and placement**: "80% exists" is the headline finding in 08, the thesis sentence in 07, and a pro in 04 — while the load-bearing caveat ("existence of primitives ≠ a finished product"; the glue is real work; the hard 5% carries the risk) is consistently the _second_ sentence or a §6/§7 con. A skim reader (an exec) takes away "mostly built." Critically, doc 08 §2's inventory counts **codegen-domain** assets (39 agents, 70 rules, the PACT/EATP/aegis governance) as "the 80% of _this_ platform" — but those are governance/artifact _primitives_, not enterprise-work capability. The re-targeting from "governing an agent that writes code" to "governing an agent doing arbitrary enterprise work" is itself flagged as "an inheritance claim with integration risk" (`02` Appendix B.2, `08`-research §3.4) — yet that risk is not discounted from the 80% number.
- **WHY IT MATTERS:** "80% exists" is the reuse-economics claim that makes the whole venture look cheap and fast (it directly feeds the CFO pitch in `02` §1.3 P8 and the "time-to-first-capability is short" implication in `08` §6.2). If a reader underwrites the build cost on "80% done" and the real number for _enterprise-work_ capability (not codegen primitives) is materially lower once integration glue + re-targeting + the net-new 5% are counted, the plan is mis-budgeted. The docs are honest in their cons but the _arithmetic of the headline_ is not risk-adjusted.
- **FIX:** Add a single explicit sentence wherever "80% exists" leads: "**80% of the _primitives_ exist; the _enterprise-work product_ is materially less complete once integration glue and the codegen→enterprise re-targeting are counted — the 80% is a reuse claim about building blocks, not a completion claim about the product.**" Doc 08 already has the words (§0, §6.2 con, §7.1) — promote them to sit _adjacent to_ the headline, not three sections later. Optionally split the inventory: "80% of governance/artifact _primitives_" vs "X% of enterprise-work _capability_" so the codegen-vs-enterprise gap is visible in the number itself.

### H-2 — The Cowork threat is named but its _trajectory_ is under-weighted; the docs treat Cowork's substrate gaps as static

- **SEVERITY: HIGH**
- **LOCATION:** `02` Part 3; `03` §0 + §2.3/§3.3 (Cowork-misses-THIS columns); `04` §2.2 implications; `05` Part 4 honest-threat; `07-transparency` §1; `09` §5. Grounded on research `07` §3/§10.1.
- **WHAT'S WRONG:** Every doc correctly says "do not compete on the surface; compete on the substrate Cowork has not productized (M1/M2/M3/M4)." But research `07` §10.1 itself records that Cowork ships **"12 features in ~12 weeks"** and **"iterates every ~2 weeks"** — and the analysis treats Cowork's _current_ substrate gaps (no versioned cascade, single-human, lighter governance) as a stable moat boundary. The risk doc `09` §5 is the _only_ place that takes convergence velocity seriously (it lists "surface convergence" and "hyperscaler ships M1/M3" as risk 5). Docs 02/03/04/05 each lean on "Cowork doesn't do X" as a present-tense differentiator without carrying `09`'s caveat that X is "the gap to productize, not invent" (research `07` §2 on LangGraph time-travel) — i.e. the mechanism is OSS and a fast-shipping incumbent could close the gap inside the build horizon. The whole moat is "unoccupied _now_"; "now" is doing a lot of load-bearing work that only `09` discloses.
- **WHY IT MATTERS:** The entire positioning ("lead with the substrate Cowork hasn't built") is a race against a competitor explicitly documented as the fastest shipper in the category. If M1 (the lead USP) is "the gap to productize, not invent" _for everyone_ — including Anthropic — then leading the _story_ with M1 while _shipping_ M2 first (the `03` recommendation) means the platform markets its headline on the one term most likely to be taken by a faster incumbent. The analysis is internally aware of this (`09` §5, §9 "2+5" interaction) but the value-prop and USP docs that a buyer/investor reads first do not carry the velocity caveat.
- **FIX:** Add to `03` §8 and `02` Part 3 a one-line forward-looking caveat cross-referencing `09` §5: "Cowork's substrate gaps are present-tense and Cowork is the category's fastest shipper; the M1/M3 moats are 'unoccupied now,' and the competitive window (un-sized — `09` open-question 1) is the binding constraint on the lead-with-M1 story." This is honest and it is already true in `09`; it just needs to travel to the front-of-funnel docs.

### H-3 — "Versioned cascade re-run, only affected downstream recompute" is presented as an architecture-grade promise but rests on a content-fingerprint assumption that LLM non-determinism partially breaks

- **SEVERITY: HIGH**
- **LOCATION:** `03` §2.2 (the moat), `07-transparency` §3.2 ("only recompute what changed" guarantee), §5.1 step 4 ("If the new fingerprint equals the recorded one, it skips"), §5.3.
- **WHAT'S WRONG:** The cascade-minimality guarantee (`07` §3.4 invariant 4, §5.1 step 4) is: recompute a step's input-fingerprint; if unchanged, skip. This is sound for deterministic steps. But for **model steps**, `07` itself (§5.3) establishes that a re-run "may legitimately differ" — meaning a model step's _output_ fingerprint can change even when its _input_ fingerprint is identical, if the user opted to regenerate. The "only affected downstream" promise (the headline that makes the feature feel cheap and safe) holds cleanly only when downstream steps reuse _recorded_ outputs; the moment a regenerate cascades, a single re-rolled model step can dirty an arbitrarily wide subtree whose inputs "didn't change" in the fingerprint sense but did change in the answer sense. Doc 07 handles this honestly in §5.3 (re-run vs replay vs branch) and §8 (cascade cost explosion) — but the _moat statement_ in `03` §2.2 and the _guarantee_ framing in `07` §3.2 do not carry the asterisk. The "leaving steps 1–3 untouched" example in `03` §2.1 is the deterministic happy path.
- **WHY IT MATTERS:** This is the lead USP. If the headline ("change step 4, only step-4's dependents recompute, everything else is untouched") is materially weaker than stated for the non-deterministic case — and non-deterministic model steps are the _whole point_ of an agentic platform — then the lead USP's most quotable promise is an over-claim in exactly the place it will be demoed. The `09` doc ranks this risk #2 and recommends shipping a _reduced_ M1; but `03` (the USP doc that defines the lead) markets the full version.
- **FIX:** In `03` §2.1/§2.2 add the determinism asterisk that `07` §5.3 already contains: "the 'only affected downstream' guarantee is clean when downstream reuses recorded outputs; when the user _regenerates_ a model step, downstream may legitimately re-derive — so the promise is 'only the steps that actually changed,' where 'changed' includes an explicit regenerate choice, not 'only the one step you edited.'" Align the lead-USP claim with `09`'s reduced-M1 v1 (linear retrace, reuse-recorded default) so the marketed USP and the shippable USP are the same thing.

### H-4 — `06-network-effects.md` imports a "five behaviors" taxonomy (ACCESSIBILITY/ENGAGEMENT/PERSONALIZATION/CONNECTION/COLLABORATION) as if canonical, but it appears nowhere in the brief or research — its provenance is unstated

- **SEVERITY: HIGH**
- **LOCATION:** `06-network-effects.md` §0–§6 (the entire doc is structured on these five), §0 "The five behaviors below are the standard decomposition."
- **WHAT'S WRONG:** The doc asserts these five are "the standard decomposition of how a platform compounds" but cites no source for the taxonomy itself — and a grep of the brief and all nine research files finds none of these five terms used as a framework (verified: zero hits in `briefs/` and `01-research/` for the five-behavior set). The doc's own §1 then immediately undercuts the taxonomy: "three of these five … are **better described as retention/lock-in than as classic network effects**" and "Calling all five 'network effects' is the marketing shorthand." So the doc adopts an unsourced five-part frame, then spends a paragraph explaining that the frame mislabels three of its five members. The substantive analysis (which loop to ignite first) is good and consistent with `04`; the _scaffolding_ is an imported, unattributed, partly-self-refuted taxonomy.
- **WHY IT MATTERS:** An analysis doc that builds its whole structure on a "standard decomposition" it neither sources nor fully endorses invites the reader to ask "standard according to whom?" — and the honest answer ("a generic platform-strategy checklist, three terms of which don't fit") undercuts the rigor of the surrounding analysis. The risk is _credibility-by-association_: the strong M4-flywheel recommendation gets framed by a weak taxonomy.
- **FIX:** Either (a) cite the taxonomy's source explicitly (if it is a known platform-strategy framework, name it; per `independence.md` name it factually), OR (b) drop the five-behavior scaffolding and restructure the doc around the two things it actually concludes are network effects (COLLABORATION/M3 within-workspace and M4 cross-org) plus the three retention loops, labeled honestly as retention from the start rather than as "network effects (but really three are retention)." Option (b) is cleaner and the doc's own §1 already argues for it.

### H-5 — The agent-comms hypothesis is well-flagged as a BET in 6 of 7 docs — but `06-network-effects.md` §6.2 states it as the operative mechanism of a flywheel diagram before flagging it

- **SEVERITY: HIGH**
- **LOCATION:** `06-network-effects.md` §6.2 (the COLLABORATION compounding-loop diagram) vs §6.3 (the flag).
- **WHAT'S WRONG:** The prompt specifically asked whether the unproven agent-comms hypothesis is ever treated as fact. Across docs it is overwhelmingly treated as a BET (excellent — see Credit C-2). The one place it slips: `06` §6.2's flywheel diagram embeds **"coordination is less lossy than human↔human comms (the brief's hypothesis)"** as a _causal step in the loop_ — "richer signed context → coordination less lossy than human comms → teams prefer to work HERE." The diagram presents the unproven premise as a working mechanism that drives the team-gravity flywheel, and only the _next_ subsection (§6.3) flags it as unproven. A reader who reads the diagram and the §6.2 prose builds the mental model "this loop works because agent-comms beat human-comms" before reaching the flag. Compare `03` §4.4 and `02` §2.3, which flag the bet _inside_ the same paragraph that introduces it.
- **WHY IT MATTERS:** A flywheel is a causal claim. Putting an unproven premise inside the causal chain of the platform's #2 network effect, then flagging it afterward, is exactly the "treat the bet as fact then caveat" pattern the analysis otherwise avoids rigorously. The COLLABORATION loop's _defensible_ driver is the signed/lossless/attributable substrate (which is real DNA); the agent-comms-superiority claim is the _contested_ driver — the diagram leads with the contested one.
- **FIX:** Rewrite `06` §6.2's loop so the _proven_ driver (lossless signed shared context, cryptographic attribution) is the causal mechanism and the agent-comms-superiority claim is marked **[BET]** inline at the arrow where it appears, not deferred to §6.3. The substrate-gives-team-gravity loop stands on its own without the contested premise.

---

## MEDIUM

### M-1 — No single doc states the relationship between the "lead USP" (M1), the "primary transaction" (M4-artifact), and "lead-with-Augment" — a two-doc reader can build a contradictory model

- **SEVERITY: MEDIUM** (this is **F-A1/F-A2** from the consistency table)
- **LOCATION:** `03` §8.1 (lead M1), `04` §2.2 (primary transaction B/M4), `05` §5.1 (lead Augment), `06` §8.1 (primary flywheel M4).
- **WHAT'S WRONG:** Each of these is internally correct and they do NOT actually contradict (M1 = the differentiating _capability_ you lead the story with; M4 = the _network-effects engine / primary platform transaction_ sequenced second; Augment = the _value-axis_ ≈ M1+M2 you lead the wedge demo with). But the word "lead"/"primary" is overloaded across four docs with four referents (lead USP-story, primary transaction, primary flywheel, lead value-axis) and **no doc maps the four onto each other**. A reader who reads only `04`+`05` sees "primary = the artifact transaction" and "lead = Augment" and cannot tell that the _headline pitch_ is M1 (which is in `03`). A reader of `03`+`06` sees "lead = M1" and "primary = M4" with no statement that these are different roles, not competing answers to the same question.
- **WHY IT MATTERS:** The prompt's exact concern — "does the platform-model's 'primary transaction' cohere with network-effects' 'primary flywheel' and USPs' 'lead USP'?" The answer is _yes, they cohere_, but only to a reader who holds all four docs in their head and disambiguates "lead"/"primary." That is too much to ask. A skim reader will perceive a contradiction that isn't there.
- **FIX:** Add a 4-row "role map" to the strategic-spine/summary surface (or the top of `03`, the USP doc): _Lead USP (story) = M1; Ship-first (foundation) = M2; Lead value-axis (demo) = Augment (≈M1+M2); Primary transaction / network-effects engine (sequenced 2nd) = M4._ One table kills the ambiguity. Reuse the disambiguation `03` §8.1 already does for M1-vs-M2 ("the story you tell vs the ground you stand on").

### M-2 — Effort sizing in autonomous cycles compounds optimistically; the docs never sum the net-new work or surface the critical-path total

- **SEVERITY: MEDIUM**
- **LOCATION:** `03` §2.4 (~4–6 cycles M1), `05` (qualitative), `06` §8.5, `07` §6.3 (per-item cycle counts), `08` §6.1 (the sizing table).
- **WHAT'S WRONG:** Every doc dutifully sizes in autonomous-execution cycles (per the rule, good). But the sizings are always _per-item_ and always "~1 session / ~1–2 cycles / ~3–5 sessions." No doc sums them or identifies the _serialized critical path_ — and several items are explicitly gated (the registry is "gated on the trust model landing first," `06` §8.3; the runtime-ownership spike "must run before the runtime is committed," `09` §10). The throughput-multiplier framing ("parallelize the 80%," `08` §6.2) is applied to assembly, but the _gated_ net-new items (trust model → registry; spike → runtime → M1) are inherently serial and their sum is never stated. The reader is left with an impression of many cheap parallel sessions and no honest critical-path number.
- **WHY IT MATTERS:** `autonomous-execution.md` forbids human-day estimates but does NOT forbid honest aggregate sizing in cycles — and a strategy doc that sizes 12 items at "~1–5 cycles" each without a critical-path sum lets the reader infer "small" when the _serial_ chain (spike → runtime decision → M2 wiring → L3 cascade → legibility validation → reduced-M1) could be the binding timeline. This interacts with H-2 (competitive window): an un-summed critical path against an un-sized window (`09` open-question 1) is two unknowns multiplied.
- **FIX:** Add a critical-path sequence (not a sum-of-all-cycles, which would imply false serialism) to `08` §6.2 or `09` §10: name the _serial_ chain of gated net-new items and its cycle range, distinct from the parallel assembly. The `09` §10 "sequence in one picture" is close — extend it with the cycle range on the serial spine.

### M-3 — `04-platform-model.md` cold-start solution leans on "seed the marketplace with the existing 400+ artifacts," but the same doc admits they are codegen artifacts that seed no demand

- **SEVERITY: MEDIUM**
- **LOCATION:** `04` §6.1 ("Seed the supply side with the ecosystem's existing 400+ artifacts") vs its own symmetric con (§6.1 end: "the 400+ seed artifacts are _codegen_ artifacts … a finance buyer sees an empty finance shelf").
- **WHAT'S WRONG:** §6.1 is titled and led as a cold-start _avoidance strategy_ ("Seed the supply side with the ecosystem's existing 400+ artifacts") and only at the end concedes the seed "prove[s] the machinery but … do[es] not seed demand in any non-coding vertical." So the headline mitigation (seed with 400+ artifacts) is, by the section's own admission, **not a mitigation for the actual cold-start problem** (which is demand-side and per-vertical). The real cold-start answer is §6.3 (intra-org-first, supply=demand=same customer) — which IS sound — but the doc ranks the codegen-seed as strategy #1 of 3, giving it billing it doesn't earn.
- **WHY IT MATTERS:** Cold-start is named "the existential risk for any platform thesis" (`04` §6). Presenting a non-solution (codegen seed) as the first listed avoidance strategy weakens the credibility of the genuinely-good third strategy (intra-org bootstrap). A skeptic reads "their #1 cold-start answer is artifacts no buyer wants" and discounts the rest.
- **FIX:** Demote the 400+-artifact seed from "cold-start avoidance strategy #1" to what it actually is — "proof the machinery works at scale" (a _de-risking_ fact, not a _cold-start_ fact) — and promote §6.3 (intra-org-first) to the lead cold-start strategy, since it is the one that actually dissolves the chicken-and-egg. Doc 04's §6 recommended sequence already gets the ordering right; the _section numbering and billing_ contradicts it.

### M-4 — Tenant-isolation vs cross-org-permeability is correctly named a "permanent tension" but the M4 cross-tenant-grant model that resolves it is repeatedly deferred without an owner

- **SEVERITY: MEDIUM**
- **LOCATION:** `06` §4.3 (the tension), `04` §9 open-question 5, `09` §4.4 (con: "M4 needs an additional explicit cross-tenant-grant model that tenant-isolation.md does not cover, which is net-new design").
- **WHAT'S WRONG:** Three docs independently identify that the M4 cross-org exchange _intentionally_ crosses the tenant boundary that the platform's whole security model is built to defend, and that resolving this needs a **net-new cross-tenant-grant model** beyond the shipped `tenant-isolation.md` discipline. All three flag it; none assigns it to the build plan or sizes it. It sits adjacent to the untrusted-publisher trust model (which IS sized and design-first'd) but is a _distinct_ problem (publisher-trust ≠ tenant-permeability) and is not folded into that work item anywhere.
- **WHY IT MATTERS:** M4 is the primary network-effects engine and the primary platform transaction. Its single most dangerous property (deliberately crossing the isolation boundary that one leak would make a company-ending headline, per `09` §4.4) has a named-but-unowned, net-new, un-sized design dependency. An un-owned dependency on the highest-value/highest-risk surface is how the orphan/Phase-5.11 pattern starts.
- **FIX:** Add the cross-tenant-grant model as an explicit, design-first work item alongside the untrusted-publisher trust model in `08` §6.1's table and `06` §8.4 Stage-2, with the note that it is _distinct from_ publisher-trust (one governs _who_ can publish; the other governs _how_ an artifact legitimately crosses a tenant boundary). Size it (greenfield) so it is not invisible.

### M-5 — The "learning loop generalizes from answers to artifacts" leap is the load-bearing assumption behind the whole flywheel/feeder thesis, and it is asserted across docs as "the platform's real build" without a feasibility argument

- **SEVERITY: MEDIUM**
- **LOCATION:** `04` §2.2 ("Generalizing D from 'learns answers' to 'learns artifacts' is the stated gap"), §9 open-question 3 ("[UNCERTAIN] Does D generalize from answers to artifacts?"); `06` §3.3 con + §8.6 con; `05` §3.3 worked example.
- **WHAT'S WRONG:** The flywheel (`04` §2.2) and the seed-inventory thesis (`06` §8.4 Stage-1) both depend on the comms wedge's proven _data-level_ learning loop (human answer → knowledge chunk) generalizing to _process-level_ artifact capture (observed work → reusable skill/rule). Every doc correctly flags this as unproven (`04` §9.3 [UNCERTAIN], `06` §3.3, §8.6). But the docs that _recommend_ the within-org loop as the no-cold-start Stage 1 (`06` §8.1) treat it as the _safe_ stage — when its core mechanism (process-artifact capture) is, by the same docs' admission, "unbuilt and unproven" (`06` §8.6 con). So the "no cold-start gap, runs today" Stage 1 actually contains a net-new unproven capability at its heart.
- **WHY IT MATTERS:** The two-stage ignition's whole appeal is "Stage 1 ships on the proven comms substrate, no cold-start risk." If Stage 1's _seed-generation_ mechanism (process-artifact capture) is unbuilt, then Stage 1 is not the safe proven loop it is billed as — it is "proven trust/feedback spine + unproven process-artifact capture." The flag exists; the _billing of Stage 1 as the safe stage_ under-weights it.
- **FIX:** In `06` §8.1/§8.4 relabel Stage 1 honestly: "proven trust/feedback/transparency spine + **net-new process-artifact capture** (the one unproven piece in Stage 1)." Add a cheap feasibility probe (can `/codify`-from-observed-work produce a usable non-coding artifact at all?) as the Stage-1 gate, paralleling `09`'s spike-first discipline.

---

## LOW

### L-1 — "Curated, not open" marketplace recommendation depends on a human-classify gate the same doc admits doesn't scale

- **SEVERITY: LOW**
- **LOCATION:** `04` §7.1 (curated, Gate-1 human-classify) vs §7.3 con + §9 open-question 2 (human-classify bottleneck at marketplace scale, substrate designed for ~12 operators).
- **WHAT'S WRONG:** The recommended marketplace shape (curated, human-classified) rests on the Gate-1 human-classify discipline, which the doc concedes (§7.3, §9.2) is designed for ~12 operators and "does not obviously survive" thousands of publishers. The doc handles this honestly (flags it, suggests partial automation) — it is a LOW because the honesty is present and the recommendation explicitly says "assumes curation can be partially automated … but the scaling is an open question."
- **WHY IT MATTERS:** Minor; the doc already discloses it. Flagged only so the spec/plan phase carries it forward as a sizing item rather than an aside.
- **FIX:** Carry the "curation-at-scale automation" into the plan as an explicit (sized) work item rather than an assumption inside the recommendation.

### L-2 — Doc 02's source ledger lists research files as "research 07/08/09" but the inline citations sometimes read "research 07 §X" where §X numbering can't be verified from the value-props doc alone

- **SEVERITY: LOW**
- **LOCATION:** `02` throughout (e.g. "research 08 §2.2," "research 07 §9c"); cross-checked against `01-research/07` and `08`.
- **WHAT'S WRONG:** The citations are dense and mostly resolve (I spot-checked research 07 §1/§3/§7/§9/§10 and they match the claims). A few section refs (e.g. "research 08 §3.5," "§5.4," "App-B.4") could not be verified without opening research 08 in full, which is outside this red-team's named scope. This is not evidence of a fabricated citation — the ones I checked are accurate — but the _density_ of §-level cross-refs creates surface area for drift if research files are renumbered.
- **WHY IT MATTERS:** Low. The citation discipline is otherwise exemplary (far better than typical). Flagged only as a maintenance risk: §-level refs are brittle under `specs-authority.md`-style re-derivation if research files change.
- **FIX:** None required now. At `/codify`, run a mechanical citation-resolution sweep (grep each `research NN §X` against the file) to catch any drift, per the spirit of `spec-accuracy.md` MUST-1.

### L-3 — "PDPA / Singapore" compliance grounding is cited as a present strength but is a comms-wedge property, not a platform property

- **SEVERITY: LOW**
- **LOCATION:** `02` §1.4 + P5, `04` §5.1/§7.3, `06` §4.3, `08` §2.1 (schema-per-tenant "passes Singapore PDPA").
- **WHAT'S WRONG:** Several docs cite the comms wedge's PDPA-clean schema-per-tenant isolation as a platform credibility anchor. It is a real, shipped, good property — _of the wedge_. The platform's M1 content-addressed ledger and M4 cross-org exchange introduce _new_ isolation surfaces (`09` §4.4 names the M1 shared-namespace vector explicitly) that the wedge's PDPA posture does not cover. The docs mostly scope this correctly (P5 says "the spine works against real users + real data") but a couple of phrasings let "PDPA-clean" read as a platform-wide fact.
- **WHY IT MATTERS:** Low; `09` §4.4 carries the real caveat. Flagged so the buyer-facing P5 claim doesn't get quoted as "the platform is PDPA-compliant" when only the wedge is, and the new platform surfaces re-open the question.
- **FIX:** Scope the PDPA claims to the wedge explicitly wherever they appear in buyer-facing prose ("the wedge is PDPA-clean; the platform's new ledger/exchange surfaces inherit the _discipline_ but must re-prove isolation on the new surfaces — `09` §4.4").

---

## CREDIT WHERE DUE (honesty already present — NOT re-flagged above)

- **C-1 — The PROVEN/CONTINGENT split in `02` is exemplary.** Every value claim is tagged, the 95%-pilot-failure stat is explicitly flagged "methodologically soft … directional, not precise" (`02` §0.3), and the $450B/95% figures are flagged directional in Appendix B. This is the honesty the rule corpus demands; do not weaken it.
- **C-2 — The agent-comms hypothesis is treated as a BET in 6 of 7 docs, rigorously.** `02` §2.3 + Part 4 #5, `03` §4.4 + §8.4, `05` Appendix B (implicitly via M3), `08` §7.6, `09` §3 (a full risk section) all flag it as unproven/contrarian and refuse to sell it as fact. Only `06` §6.2 slips (H-5). This is the strongest single piece of discipline in the analysis.
- **C-3 — The risk doc (`09`) is genuinely adversarial.** It ranks PMF ("lands nowhere") as risk #1, treats Decision B as "both a mitigation AND a risk," builds a risk-interaction map, and ends on six honest open questions. It does not pull punches on the L5-autonomy-vs-containment tension or the legibility dependency. This is what a skeptic's document should look like.
- **C-4 — M1's hardness is stated everywhere, never hidden.** "Strongest moat AND highest execution risk" appears in `03`, `05`, `07`, `09` consistently. The recommendation to ship a _reduced_ M1 first (`09` §2.4) is the right de-risking move and is honest about the expectation-gap con.
- **C-5 — Traceability-vs-accountability distinction (`07` §2.3).** Correctly states the system delivers traceability, not accountability — "we promise the glass box; we do not promise the human looked through it." This is a legally and ethically important honesty that most vendor docs omit.
- **C-6 — Effort is in autonomous cycles, not human-days, throughout** (per `autonomous-execution.md`). Compliance is consistent (the only critique is M-2: per-item sizing without a critical-path sum, which is a refinement, not a violation).

---

## VERDICT

**FIXES-NEEDED** (one BLOCKING item must be resolved before this analysis is sound).

- **BLOCKING: 1** (B-1 — the AAA framework means two different things across docs 02 and 05, with a broken cross-reference)
- **HIGH: 5** (H-1 "80% exists" over-reassures · H-2 Cowork velocity under-weighted in front-of-funnel docs · H-3 cascade "only-affected-downstream" promise vs LLM non-determinism · H-4 unsourced/self-refuted five-behavior taxonomy · H-5 agent-comms bet inside a flywheel's causal chain)
- **MEDIUM: 5** (M-1 "lead/primary" overloaded across 4 docs, no role-map · M-2 no critical-path sizing · M-3 codegen-seed billed as cold-start strategy #1 · M-4 cross-tenant-grant model un-owned · M-5 answers→artifacts leap under-billed in "safe" Stage 1)
- **LOW: 3** (L-1 curation-at-scale · L-2 §-citation brittleness · L-3 PDPA scoped to wedge)

The four core strategic claims the prompt asked me to verify (M1-leads / M2-first / within-org-then-cross-org / lead-with-Augment) are **internally consistent** — the only defect there is M-1 (the relationship between the overloaded "lead/primary" terms is never stated in one place, so a partial reader _perceives_ a contradiction that isn't real). The single must-fix is B-1; the HIGH items are over-claims that the docs already partly disclose elsewhere and need only to carry their own caveats to the front.
