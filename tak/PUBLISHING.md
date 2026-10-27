# Publishing playbook: Day 0 → Day 90

Operating manual for taking **Subdomain Takeover & Certificate Expiry Radar** from this repository to a public, monetized Apify Store listing. Every step below is either a command you can paste or a Console field with the exact value to enter.

Placeholders: `engraved_peanut` is the account name visible in your Console. Confirm it under **Settings → Account** before pushing; the Store URL is `https://apify.com/<username>/subdomain-takeover-cert-expiry-radar`.

---

## Phase 0 - pre-flight (30 minutes, blocks everything)

| # | Task | Where | Why it blocks publishing |
|---|---|---|---|
| 0.1 | Verify identity (KYC) | Console → Settings → **Payouts / Identity** | Required for payouts, >10 Actors, and to be eligible for agentic payments (x402, MPP, Skyfire) |
| 0.2 | Accept Store Publishing Terms | Console → publish flow | The **Publish on Store** button stays disabled until accepted |
| 0.3 | Billing details complete | Console → Billing | Monetization setup requires a payment method |
| 0.4 | Confirm $5–$20 prepaid usage | Console → Billing | Your own test runs on the platform are billed to you |
| 0.5 | Confirm no name clash | `https://apify.com/engraved_peanut/subdomain-takeover-cert-expiry-radar` should 404 | Actor URLs cannot be renamed after creation, so the slug must be right the first time |

The slug `subdomain-takeover-cert-expiry-radar` is 36 characters, lowercase + hyphens only, unique across your account - it satisfies the API rule ("lowercase letters, numbers, and hyphens; must be unique"). The display title is 45 characters, inside Apify's recommended 40–50 range, and carries the exact phrase buyers search for.

---

## Phase 1 - local release gate (must be green before pushing)

```bash
cd /workspace/tak
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

python -m pytest                 # offline tests, ~1s
python -m compileall -q src      # no syntax errors in the Docker image
apify validate-schema            # INPUT_SCHEMA.json + dataset schema
```

Then one live run with the exact input the Store's daily test uses (the `prefill` values):

```bash
apify run --purge
ls storage/datasets/default | wc -l    # ~40 for mozilla.org; must be > 0
```

**Hard gate:** the automated Store test runs your `prefill` input, expects **Succeeded** plus a **non-empty default dataset within 5 minutes**, and marks the Actor *Under maintenance* if more than half of runs in a rolling 3-day window fail. The default input resolves in seconds; do not raise `maxHostsPerDomain` above ~200 in `prefill`.

Optional but recommended before pricing goes live:

```bash
ACTOR_TEST_PAY_PER_EVENT=true apify run
ls storage/datasets/charging_log      # confirms 1 charge per saved record
```

---

## Phase 2 - deploy to the platform

```bash
apify login                       # or: apify login --token <APIFY_TOKEN>
apify push                        # first push CREATES the Actor on your account
```

What `apify push` does with `actor.json`: creates/updates `engraved_peanut/subdomain-takeover-cert-expiry-radar`, builds `version 1.0`, tags it `latest`, uploads `Dockerfile`, `README.md`, `.actor/INPUT_SCHEMA.json`, `.actor/OUTPUT_SCHEMA.json`, `.actor/dataset_schema.json` and `src/`.

Verify the build before touching the Store form:

```bash
apify actors info engraved_peanut/subdomain-takeover-cert-expiry-radar
apify actors call engraved_peanut/subdomain-takeover-cert-expiry-radar   # runs with prefill input
```

Check in Console → Actor → **Runs**: status Succeeded, log shows `Audited N live hosts`, **Storage → Default dataset** renders the table view from `dataset_schema.json` (if it does not, the dataset schema is the thing to fix, not the code).

**Release rhythm from here on:** bump `version` in `.actor/actor.json` (`1.0 → 1.1`) for every push. Each version keeps its builds, so rollback is a build-tag move, not a hotfix in production.


---

## Phase 3 - Store listing (Console → My Actors → Actor → Publishing tab)

Complete all five sections; the Publish button unlocks only when every section is marked done.

### 3.1 Display information

| Field | Value |
|---|---|
| Actor name (title) | `Subdomain Takeover & Certificate Expiry Radar` (45 chars) |
| SEO title | `Subdomain Takeover and SSL Expiry Scanner` (41 chars, recommended 40–50) |
| SEO description | `Scan your domains for subdomain takeover, dangling CNAMEs and expiring TLS certificates. Live DNS and certificate checks, clean JSON output.` (140 chars, recommended 140–156) |
| Description | `Live attack-surface audit: finds dangling CNAME subdomain-takeover risks and expiring, expired or invalid TLS certificates across your domains.` (143 chars) |
| Categories | `Developer tools` primary; add `Other` only if the dropdown offers no security category. API enum form is `["DEVELOPER_TOOLS"]` |
| Tags / keywords | subdomain takeover, dangling CNAME, SSL expiry, certificate expiry monitoring, TLS scanner, attack surface management, EASM, DNS security, certificate transparency, security monitoring, compliance |
| Icon | 512×512 PNG, transparent background, high contrast, under 200 KB |

Store search and the Apify MCP `search-actors` tool rank on the same quality score, and the title is the strongest keyword signal. Do not rename the title after launch unless you have data - it resets user recognition.

### 3.2 Sample output

Paste the first item of a successful run (Console → last run → Default dataset → JSON view). Prefer a **risk** row: run once with `expiryWarningDays: 70` on a domain with Let's Encrypt certificates and you get `medium` findings. A sample showing a real finding sells better than an all-`info` table:

```json
{
  "host": "addons.mozilla.org",
  "rootDomain": "mozilla.org",
  "severity": "medium",
  "findings": [
    {
      "type": "certificate_expiring",
      "severity": "medium",
      "detail": "Certificate expires in 60 days (2026-12-25T15:08:08+00:00)."
    }
  ],
  "findingTypes": ["certificate_expiring"],
  "cnameChain": [],
  "thirdPartyService": null,
  "resolvedIps": ["151.101.1.91"],
  "httpStatus": null,
  "tlsValid": true,
  "certIssuer": "Let's Encrypt",
  "certExpiresAt": "2026-12-25T15:08:08+00:00",
  "certDaysLeft": 60,
  "checkedAt": "2026-10-26T14:38:17.866218+00:00"
}
```

### 3.3 Output schema

Already wired: `.actor/OUTPUT_SCHEMA.json`, referenced from `actor.json` as `"output": "./OUTPUT_SCHEMA.json"`. An output schema is **mandatory** for Store publication and is what lets AI agents chain this Actor. Confirm the section shows green.

### 3.4 Actor permissions

Select **Limited permissions**. It is a scored quality category ("Trustworthiness"), and full permissions make the Actor ineligible for per-request agentic payments. This Actor only reads input and writes its own default dataset, so limited permissions are enough.

### 3.5 Source visibility


---

## Phase 4 - monetization (Publishing tab → Monetization → Set up monetization)

The wizard has three steps: **Actor pricing → Primary event → Review**.

### 4.1 Events to configure

| Event | Title | Price | Charged when |
|---|---|---|---|
| `apify-actor-start` (synthetic) | Actor start | `$0.005` (default) | Once per run; covers container start |
| `apify-default-dataset-item` (synthetic) | Dataset item | **Delete this event** | Would double-charge: every saved record already fires `host-audited` |
| `host-audited` (custom) | Host audited | `$0.010` | A discovered host resolves, answers a probe, and its record is written |
| `risk-finding` (custom) | Verified risk finding | `$0.120` | The saved record has `medium`, `high` or `critical` severity |

Descriptions to paste (they appear on the Actor page and drive the "Pricing transparency" score):

- `host-audited` - "One live subdomain: resolved in DNS, probed over TLS/HTTP, and returned as one verified audit record."
- `risk-finding` - "The audited host has a confirmed medium, high or critical issue: takeover risk, expired or invalid certificate, or expiry inside your warning window."

**Primary event:** `host-audited`. It is the event that best represents the product and is highlighted on the detail page.

### 4.2 Pricing decisions that matter

1. **Do not enable "pay per event + platform usage."** Charging only events keeps the Actor eligible for per-request agentic payments and keeps pricing predictable. Platform cost is roughly $0.0005 per host at 256 MB, so absorb it.
2. **Minimum max-cost per run:** set `$0.10`. A user can still run a 10-host check, but pointless sub-cent runs are blocked.
3. **Discount tiers:** if the Console offers Bronze/Silver/Gold discounts, start at 10% / 15% / 20%. It feeds the "pricing transparency" score and converts committed platform users.
4. **Significant changes are locked:** a pricing model change, any price increase, or a new paid event triggers a 14-day notice and can only be submitted **once per month** per Actor. Price decreases, event removal and description edits apply immediately. Get the first submission right; a correction costs a month.

### 4.3 Unit economics to sanity-check after week 1

Apify's formula: `profit = (0.8 × revenue) - platform costs` (Apify keeps 20%; free-plan users generate neither cost nor revenue for you).

| Scenario | Revenue | Payout (80%) | Platform cost (est.) | Profit |
|---|---|---|---|---|
| 50 hosts, no findings | $0.51 | $0.41 | $0.03 | **$0.38** |
| 50 hosts, 40 findings | $5.31 | $4.25 | $0.03 | **$4.22** |
| 500 hosts, 300 findings | $41.01 | $32.81 | $0.25 | **$32.56** |

A daily monitoring customer with 500 hosts spends roughly $1,230/month at the worst case; the same coverage is 3-5 billable consultant days per month. That gap is what you are selling into.


---

## Phase 5 - publish and verify

1. Publishing tab: all five sections green → **Publish on Store**.
2. Verify as an anonymous visitor: open `https://apify.com/engraved_peanut/subdomain-takeover-cert-expiry-radar` in a **private window** (a logged-in session hides visibility problems).
3. Verify via API:

```bash
curl -s "https://api.apify.com/v2/acts/engraved_peanut~subdomain-takeover-cert-expiry-radar?token=$APIFY_TOKEN" | jq '.data.isPublic'
```

4. Run the public page's **Try for free / Start** button once. This is the exact path a Store buyer takes. Confirm: prefill loads, run succeeds, the Output tab shows the table, and the price estimate is visible before starting.

---

## Phase 6 - Day 1 to Day 7 quality operations

The Store runs your Actor **daily with the prefill input**. That test is the single biggest driver of the "Reliability" score and of the *Under maintenance* status.

| Signal | Target | Where | Action if red |
|---|---|---|---|
| Daily test status | Succeeded every day | Console → Actor → Runs | Open the failing run's log; most failures are CT-log rate limits or a provider page change |
| Run duration | < 60 s for prefill | Run detail | Lower `maxHostsPerDomain` in `prefill` (Store limit is 5 min) |
| Dataset non-empty | always | Test run storage | Apex host is always included; if empty, TLS probing is broken |
| Quality score | climb weekly | Console → **Insights → Actor quality** | Fix the category the dashboard flags; score recalculates several times per day |
| Issues tab | 0 unanswered | Actor → Issues | Answer within 24h; unanswered issues damage the score |

Quality categories the score aggregates: reliability, popularity, feedback and community, ease of use, pricing transparency, trustworthiness, history of success, congruency of texts. Four of them are already engineered in (schemas, limited permissions, PPE-only pricing, consistent naming across title/README/input), so the score mostly tracks run success and early reviews.

Two things that *will* happen and are not bugs:
- **CT-log rate limits** (Cert Spotter unauthenticated tier). The Actor logs a warning per failed source and continues with the other source plus the apex domain, so the run still succeeds.
- **Provider fingerprint drift.** When a hosting provider rewrites its unclaimed-resource page, the takeover check stops matching. That is a signature update, not an outage: edit `TAKEOVER_SIGNATURES` in `src/main.py`, add a test case, bump to `1.1`, `apify push`.


---

## Phase 7 - growth plan (30 / 60 / 90 days)

**Day 0-30 - get the first 10 users**
- Create a **Task** preset named "Daily takeover watch" on the Actor page (`onlyRisks: true`, `expiryWarningDays: 14`). Tasks are one-click entry points on the Store.
- Schedule your own account to run it daily and wire a webhook to Slack/email so you experience the alert path before customers do.
- Publish one technical post ("Finding dangling CNAMEs with Certificate Transparency logs") linking to the Store page; the README's H2/H3 headings are what search engines and AI assistants quote.
- Post in the Apify Discord #showcase and in communities where self-promo is allowed (r/netsec, r/cybersecurity).

**Day 30-60 - make it agent-native**
- Confirm discoverability through the Apify MCP server. Test an agent prompt: *"Find actors that detect subdomain takeover and check example.com"*. Ranking follows the same quality score, so keep run success at 100%.
- Ship `1.1` with the features users actually ask for in Issues. Request-driven releases raise ease-of-use and review scores.
- Ask every user who ran it 3+ times for a review via the Issues tab. Reviews are a scored category and compound.

**Day 60-90 - price and portfolio**
- Review Console → Insights → Analytics: cost per 1,000 results, revenue per user, success rate. If cost per 1,000 results is under 10% of revenue, volume is a better lever than a price rise.
- If you add a second Actor (DNS/SPF/DMARC posture, exposed-panel discovery), cross-link the READMEs. A genuine portfolio lifts "popularity".
- Any price increase needs the 14-day notice and is limited to once per month. Plan it with a changelog entry, never silently.

---

## Phase 8 - operations runbook

| Scenario | Detection | Response |
|---|---|---|
| Daily test fails once | Console notification | Read log; usually a transient CT/DoH hiccup. Act only if the next run fails |
| Daily test fails 3 days running | *Under maintenance* badge | Reproduce with `apify run --purge`; fix, bump version, `apify push`. Status recovers within 24h of a good build |
| Provider fingerprint changed | Users report missed takeovers | Update `TAKEOVER_SIGNATURES`, add a unit test, release `1.1` |
| CT sources rate-limited | Warnings in run log | Nothing to fix; optionally add a Cert Spotter API token as a secret env var |
| Bad build in production | Errors in runs after push | Console → Actor → Builds: retag the previous build as `latest`; then fix forward |
| Charging spike / thin margin | Insights → Analytics | Recheck event prices. The SDK charge-limit stop prevents runaway runs, but a mis-set price is a business bug |
| Breaking input change planned | You want to rename/remove a field | Email community@apify.com first, keep the old field for one minor version, document in README |

SLOs: **≥ 98% successful runs**, **p95 duration < 60 s** for the prefill workload, **< 24 h** first response on Issues, and at least one release per month (the Store surfaces "recently modified"). Reserve about **2 hours per week** for maintenance, as Apify recommends for public Actors.

---

## Phase 9 - CI and repository layout

`tak/ci/actor-ci.yml` is a ready GitHub Actions workflow: offline pytest, byte-compile, and `apify validate-schema` on every push that touches the Actor. It is shipped as a template rather than in `.github/workflows/` because pushing workflow files requires the `workflows` permission on the token used here. To enable it:

```bash
mkdir -p .github/workflows
cp tak/ci/actor-ci.yml .github/workflows/actor-ci.yml
git add .github/workflows/actor-ci.yml && git commit -m "ci: enable actor pipeline" && git push
```

If you later prefer **GitHub integration** over `apify push` (Apify builds from a repo on push), the Actor must sit at the **repository root**, because the integration reads `.actor/actor.json` from the default branch. Today the Actor lives in `tak/`, so either keep deploying with `apify push` (simplest, works now), or split it into a dedicated repo:

```bash
git subtree split --prefix=tak -b actor-split
git push git@github.com:<you>/actor-subdomain-takeover-radar.git actor-split:main
```

Then Console: Actor → **Source** → Git integration → connect the new repo. Note that `name`, `version` and `buildTag` in `actor.json` are used by the CLI, not by Git integration.

---

## Final pre-publish checklist

- [ ] KYC verified, Store T&C accepted, billing set, $5+ prepaid usage
- [ ] `python -m pytest` green, `apify validate-schema` green
- [ ] `apify run --purge` produces more than 5 records with prefill input
- [ ] `apify push` succeeded, platform run Succeeded, dataset table renders
- [ ] Title 45 chars, SEO title 41, SEO description 140, icon uploaded
- [ ] `apify-default-dataset-item` **deleted**, `apify-actor-start` plus two custom events priced
- [ ] Primary event = `host-audited`
- [ ] Limited permissions selected, output schema present, sample output pasted
- [ ] Private-window Store URL loads, API returns `isPublic: true`
- [ ] Daily schedule + Slack webhook running on your own account

Leave **Hide source files** checked unless you want the Open Source Fair Share revenue share. Your code stays private either way; unchecking only exposes it on the detail page.
