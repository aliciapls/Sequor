# 12 — SaaS 2.0: The Governed Agentic-Services Thesis (grounded)

> **What this is.** The strategic foundation for Sequor's repivot. It states the "SaaS 2.0" thesis and
> then grounds every load-bearing claim in 2025–2026 market evidence gathered via four parallel
> web-research passes (adversarially checked; sources cited inline). It is deliberately honest about
> what the evidence makes **ESTABLISHED**, what is **CONTESTED**, and what remains a **SPECULATIVE bet** —
> because two of Sequor's repivot pillars fall in the last bucket, and naming them is the point.
>
> **Supersedes/amends:** the "workers become builders" framing in `briefs/01-vision.md §3a` and the
> `08-product-focus`/roadmap treatment of the non-coder surface. It re-centers the product on
> **director-not-builder + integrate-not-replace + governance-as-the-product**. It also informs the
> Sequor-vs-Praxis reconciliation (`11-sequor-vs-praxis-comparison.md`, `.session-notes` F4): the
> evidence favors **Sequor's integrate-and-govern stance over Praxis's replace-the-suite stance.**

## 1. The thesis in one paragraph

"SaaS is dead" is the wrong frame. SaaS is a **stack of layers**, and autonomous AI hits each
differently: the **system-of-record / data tier hardens** (agents need trusted, governed, permissioned
data _more_ than humans did), while the **workflow / business-logic / app tier dissolves** into an agent
orchestration layer. Value migrates out of "UI + workflow lock-in + per-seat licences" and into five new
places: **trusted data/memory · agent orchestration · governance/trust/evals · governed capability
distribution · outcome delivery.** Critically, **workers do not become builders** — a thin, hugely-
leveraged specialist class (and vendors, and the platform) build governed agentic capabilities; the
**many consume them as outcomes, as _directors_ who approve, inspect, steer, and correct.** SaaS 2.0 is
therefore the **governed agentic-services layer that sits _on top of_ the surviving systems of record**,
delivering outcomes to non-builder directors — not the graveyard of software, and not a citizen-developer
utopia.

## 2. The layer model — what dies, what hardens (grounded)

| Layer                               | Fate                                                                                           | Evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ----------------------------------- | ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **System of record (data)**         | **Hardens.** Data gravity intensifies; agents deepen dependence on centralized, governed data. | Deloitte: wholesale SaaS replacement "won't be in 2026… at least five years or more" ([Deloitte](https://www.deloitte.com/us/en/insights/industry/technology/technology-media-and-telecom-predictions/2026/saas-ai-agents.html)); "data gravity" consensus ([WWT](https://www.wwt.com/wwt-research/the-ai-data-war-winning-the-battle-for-enterprise-data-supremacy)); Benioff: "without clean, connected, trusted data there is no intelligence — only hallucination" → Salesforce bought **Informatica** (Nov 2025) ([CIO](https://www.cio.com/article/4102862/salesforces-agentforce-360-gets-an-enterprise-data-backbone-with-informaticas-metadata-and-lineage-engine.html)).                                                                                      |
| **Workflow / business-logic / app** | **Dissolves / reprices.** Logic migrates up to an agent tier; per-seat model erodes.           | Nadella (BG2, Dec 2024), _actual_ quote: business apps are "CRUD databases with a bunch of business logic… the business logic is all going to these agents… all the logic will be in the AI tier" — logic first, back-ends "later" ([Podcast Notes](https://podcastnotes.org/bg2-with-bill-gurley-and-brad-gerstner/)); Salesforce Agentforce cycled through **3+ pricing models in ~18 months** (per-conversation → flex credits → pay-per-resolution) and Futurum names **"seat erosion"** as the live risk ([SaaStr](https://www.saastr.com/salesforce-now-has-3-pricing-models-for-agentforce-and-maybe-right-now-thats-the-way-to-do-it/), [Futurum](https://futurumgroup.com/insights/salesforce-q3-fy-2026-ai-agents-data-360-lift-bookings-and-fy26-outlook/)). |
| **Interface (UI)**                  | **Inverts:** data-entry → oversight/approval/inspection.                                       | Standard runtime pattern is "pause at a decision point, route approval to a human, log every intervention" ([Galileo](https://galileo.ai/blog/human-in-the-loop-agent-oversight)). _(Direction established; "the screen HAS become an oversight surface" is not yet independently measured — §5.)_                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| **Integration / orchestration**     | **Contested prize.** Either agents own it (the bet) or incumbents do.                          | Every incumbent is layering agents **on top** of its SoR and rebranding "system of action" (below).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |

**The single loudest signal:** _no major incumbent is replacing its own app tier or its data tier_ —
Microsoft ("systems of action," **Dataverse** + MCP bridges — [Ignite 2025](https://www.microsoft.com/en-us/microsoft-365/blog/2025/11/18/microsoft-ignite-2025-copilot-and-agents-built-to-power-the-frontier-firm/)), SAP Joule ("operational layer across systems… close to systems of record" — [Bersin](https://joshbersin.com/2025/10/sap-jumps-ahead-in-ai-agents-with-joule-hcm-features-and-more/)), ServiceNow ("opens its full **system of action**… Fabric connects any agent via MCP down into the systems of record" — [ServiceNow](https://newsroom.servicenow.com/press-releases/details/2026/ServiceNow-opens-its-full-system-of-action-to-every-AI-Agent-in-the-enterprise/default.aspx)), Salesforce (Agentforce 360 + Informatica). **They are defending the data tier and repricing the app tier — which tells you exactly where value is consolidating: data + orchestration + governance.**

## 3. The evidence ledger (honest split)

### ESTABLISHED (bet on these)

1. **Systems of record survive near-term (≥5 yrs) and are defensible** (Deloitte; data-gravity consensus).
2. **Incumbents layer agents _on top_ of SoRs, not replace** — uniform across Microsoft/SAP/ServiceNow/Salesforce; MCP is the connective tissue; A2A interop targeted (~Q4 2026).
3. **The app/logic tier is the vulnerable, repricing layer; value moves seat → outcome/consumption** (Nadella's real quote; Agentforce pricing thrash; "seat erosion" as a named risk).
4. **The builder fallacy is real.** No-code "last-mile" plateau survived the AI transition; **METR RCT** — experienced devs **19% _slower_** with AI while _feeling_ 20% faster ([METR](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/)). ~45% of AI-generated code carries vulnerabilities; 170/1,645 Lovable apps leaked personal data. What democratized is **low-stakes assembly + consumption**, not durable building.
5. **A thin specialist builder class does the load-bearing work** — the **Forward-Deployed Engineer** model is now the explicit GTM of OpenAI, Anthropic, AWS ($1B unit, Jun 2026), Palantir ([Pragmatic Engineer](https://newsletter.pragmaticengineer.com/p/forward-deployed-engineers), [CNBC](https://www.cnbc.com/2026/06/30/aws-amazon-ai-forward-deployed-engineers.html)); "AI engineer" is LinkedIn's #1 fastest-growing role. _(If agents let anyone build, labs wouldn't race to embed their scarcest humans.)_
6. **Enterprise core = integrate-and-govern over incumbents** — **61% of CIOs prefer buying AI from vendors they already use** ([SaaStr](https://www.saastr.com/cioreplaceai/)); **Menlo Ventures (n=495): build-vs-buy swung to 76% _bought_** (2024: 53%) ([Menlo](https://menlovc.com/perspective/2025-the-state-of-generative-ai-in-the-enterprise/)).
7. **Service-as-software is a real strategic + pricing shift** — Foundation Capital ("software becomes the worker itself"), Sequoia ("a copilot sells the tool; an autopilot sells the work" — [Sequoia](https://sequoiacap.com/article/services-the-new-software/)); **Intercom Fin's $0.99/resolution** is the clean, live, billable proof ([Fin](https://fin.ai/pricing)).
8. **Evals / agent-reliability tooling is a funded value layer** — Arize **$70M Series C**, plus Braintrust/Galileo/LangSmith/Fiddler ([Galileo](https://galileo.ai/blog/best-ai-agent-observability-platforms)).
9. **Oversight/audit is the #1 cited enterprise requirement _and_ barrier** — McKinsey: ~2/3 cite security/risk as the top barrier; only ~30% "governance-ready." **Gartner AI TRiSM + "Guardian Agents"** is a named category (predicted **10–15% of the agentic market by 2030**); ~**$3.6B** into agentic-security startups ([Gartner](https://www.gartner.com/en/articles/ai-governance-trism), [OpsInSecurity](https://www.opsinsecurity.com/blog/gartner-market-guide-guardian-agents)).
10. **Hard, dated regulatory tailwind:** **EU AI Act Article 14** legally requires effective human oversight of high-risk AI; **high-risk obligations apply from 2 Aug 2026** ([Art. 14](https://artificialintelligenceact.eu/article/14/), [timeline](https://artificialintelligenceact.eu/implementation-timeline/)). NIST AI RMF + Singapore's Model AI Governance Framework for Agentic AI reinforce (multi-jurisdiction).

### CONTESTED (hold as directional, watch closely)

- **How much/how fast the app tier erodes** — no verified case of an enterprise ripping out a core SoR; incumbent _app_ vendors are _capturing_ agent revenue (Agentforce ~$1.4B Data360+Agentforce, +114% YoY). Klarna's "replaced SaaS with AI" was **walked back by its own CEO** ("might be the opposite… SaaS will consolidate"; they built their _own_ Neo4j system of record) ([TechCrunch](https://techcrunch.com/2025/03/04/klarna-ceo-doubts-that-other-companies-will-replace-salesforce-with-ai/)).
- **"Outcome pricing is the _dominant_ model"** — the biggest verifiable revenue (Harvey ~$300M ARR) is still **seat-based**; attribution + COGS-on-failures + forecasting objections are real; **11x** was exposed for ARR inflation ("AI's Theranos moment" — [TechCrunch](https://techcrunch.com/2025/03/24/a16z-and-benchmark-backed-11x-has-been-claiming-customers-it-doesnt-have/)).
- **"Moat migrates to orchestration/trust"** — one credible _independent_ source (Berkeley [CMR](https://cmr.berkeley.edu/2026/06/the-ai-moat-is-migrating-and-most-leaders-are-looking-in-the-wrong-place/)) + valuation patterns; otherwise VC-forecast, no durable retention data, and **model labs are moving up-stack** (agent frameworks, memory, evals) — the orchestration layer could be squeezed from above.
- **Whether the governed layer is a standalone startup category or absorbed by incumbents building native governance** — _the central strategic risk to the whole thesis_ (Deloitte's "SoRs are defensible" implies incumbents build governance on the data they own).

### SPECULATIVE (these are _bets_, not facts — validate before betting the company)

- **The trillion-dollar TAMs** ($4.6T Foundation / $6T Sequoia) are **asserted, not derived** — total labour/services spend, not obtainable market. Viral ≠ validated.
- **"The human screen has _already become_ an oversight surface"** — direction real, magnitude unmeasured; the honest counter is that approval surfaces are _under-built_ relative to agent activity, and degrade into rubber-stamp at volume.
- **The "non-builder DIRECTOR" as a recognized buyer/segment** — **no evidence** a distinct non-builder-director oversight buyer is recognized or budgeted in 2025–26; today's oversight tooling sells to **technical** platform/security/AI-governance teams. **This is the single most speculative pillar of Sequor's repivot.**

## 4. The correction the evidence forces (vs. the prior Sequor framing)

The old vision leaned on **"non-coders configure objectives / workers become builders."** The evidence
says that is the _weakest_ premise. Replace it with:

> **Workers don't become builders — they become _directors_ of governed agentic services.** A thin builder
> class (internal FDEs + vendors + the platform) produces governed capabilities; the many **consume them
> as outcomes**, approving/inspecting/steering/correcting. **The product for that majority IS the
> governance surface** — because consuming work you didn't build is impossible without transparency, undo,
> posture, and audit.

This _strengthens_ Sequor's four moat pillars: M1 (undo/trace), M2 (posture governance), and audit stop
being "features" and become **the mass-market product** for directors. And it resolves the
Sequor-vs-Praxis fork on the merits: **integrate-and-govern _over_ surviving systems (Sequor's leap-2
thesis) rides the best-evidenced fact; replace-the-suite (Praxis) fights it.**

## 5. Implications for Sequor (the five highest-confidence moves)

1. **Lead with integrate-and-govern; make the systems of record your moat, not your enemy.** Read/write _through_ SAP/Salesforce/ServiceNow; derive trust from their data lineage. Any "replace your SaaS" framing fights the strongest evidence in the corpus.
2. **Make audit-trail + approval-routing the _core_ product, priced as compliance, not convenience.** The one hard, dated tailwind is **EU AI Act Art. 14 (Aug 2026 high-risk)**. Ship "accountability lineage from every agent action back to a named human" as a first-class, **exportable** artifact — a budget line with a deadline, not a nice-to-have.
3. **Risk-tiered oversight as the default UX (HITL for high-risk, HOTL for the rest) — and engineer explicitly against the rubber-stamp failure mode** (confidence scoring, exception surfacing, batch-with-sampling). "Meaningful steering at scale" is the answer to the strongest counter-argument against the oversight thesis.
4. **Assume incumbents ship native governance; win on cross-vendor _neutrality_ + the non-technical steward.** Your defensible wedge is the two things incumbents structurally under-serve: (a) **one approval/audit surface spanning _multiple_ systems of record**, and (b) a genuinely **non-builder-director-usable** interface (plain-language policies, business-risk thresholds, no code). **Validate the director persona early — it's the most speculative pillar.**
5. **Underwrite for a 40%-cancellation / "agent-washing" environment** (Gartner: >40% of agentic projects cancelled by 2027; only ~130 vendors "real"). Sell **"control that lets you deploy" + provable ROI** — position as the thing that _unblocks_ stalled agent projects (the ~2/3 citing risk as the top barrier), not another autonomous-agent add-on.

## 6. The two things to validate before scaling the bet

1. **The director persona** — does a non-builder line-of-business "director" actually exist as a _buyer/user_ of an oversight surface, or does budget sit with technical governance teams? (Cheapest test: the comms wedge already has a "human backup approving AI drafts" — that human _is_ a proto-director. Instrument it.)
2. **Standalone-vs-absorbed** — will cross-vendor neutrality + non-technical usability be enough moat when SAP/Salesforce/ServiceNow ship native governance on the data they own? (Watch: A2A interop, incumbent guardian-agent features, whether multi-SoR oversight is a real unmet need.)

## 7. Sources (primary/credible; full inline above)

Nadella BG2 transcript (Podcast Notes); Benioff / Salesforce–Informatica (CIO, Salesforce); Klarna walk-back (TechCrunch, CX Today); incumbent "system of action" (Microsoft Ignite, Josh Bersin on SAP/ServiceNow, ServiceNow newsroom); Agentforce pricing (SaaStr, Salesforce Ben, Futurum); METR RCT (metr.org / arXiv 2507.09089); FDE model (Pragmatic Engineer, CNBC, The New Stack); Menlo Ventures 2025 State of GenAI (n=495); CIO buy-preference (SaaStr); Foundation Capital "Service-as-Software" & "System of Agents"; Sequoia "Services: The New Software"; Intercom Fin pricing; Sierra/Bret Taylor (Cheeky Pint, Sacra); 11x (TechCrunch); Berkeley CMR "AI Moat Is Migrating"; Arize/Galileo/Braintrust; Gartner AI TRiSM / Guardian Agents / agentic-cancellation; McKinsey AI-trust; Deloitte SaaS-AI-agents predictions; EU AI Act Art. 14 + implementation timeline; NIST AI RMF; Singapore IMDA MGF for Agentic AI.

_Evidence-quality caveat: incumbent momentum figures are company-reported; TAM numbers and "the screen has shifted" claims are directional/vendor-adjacent; the load-bearing hard evidence is the EU AI Act primary text, Gartner/McKinsey/Deloitte, METR, and Menlo (n=495)._
