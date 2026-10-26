# Subdomain Takeover & Cert Expiry Radar

Live attack-surface audit for security, DevOps and MSP teams. Give it root domains; it discovers every subdomain from public Certificate Transparency logs, resolves DNS over HTTPS, probes TLS and flags the issues that cause real outages and breaches:

- **Subdomain takeover**: CNAME pointing at an unclaimed GitHub Pages, Heroku, S3, Azure, Shopify, Netlify and similar resource, confirmed by the provider's "unclaimed" page.
- **Dangling CNAME**: the CNAME target no longer exists in DNS (NXDOMAIN).
- **Invalid or expired certificates**: failed validation, hostname mismatch, expired chain.
- **Expiring certificates**: configurable warning window, default 30 days.

Every result is checked live at run time. No mock data, no cached lists.

## Who uses it
- Security teams running scheduled external attack-surface monitoring.
- MSPs and agencies watching client domains.
- M&A and due-diligence analysts screening a target's hygiene.
- AI agents (via MCP) answering "is any subdomain of X at risk?".

## Pricing (pay per event)
| Event | Price | Charged when |
|---|---|---|
| Host audited | $0.01 | A discovered host resolves and answers a probe, and its record is saved |
| Verified risk finding | $0.12 | The record has medium, high or critical severity |

Healthy hosts cost one cent. Turn on **Return only risky hosts** to pay only for findings. Hosts that do not resolve are never charged.

## Input
| Field | Type | Default | Description |
|---|---|---|---|
| `domains` | string[] | `["mozilla.org"]` | Root domains to audit (only ones you are authorised to test) |
| `maxHostsPerDomain` | integer | 40 | Cap on hosts audited per domain |
| `expiryWarningDays` | integer | 30 | Flag certificates expiring within N days |
| `onlyRisks` | boolean | false | Skip healthy hosts |
| `concurrency` | integer | 10 | Parallel audits (1-30) |
| `probeTimeoutSecs` | integer | 8 | TLS connect timeout |
| `proxyConfiguration` | object | none | Optional proxy for HTTP and discovery |

## Output sample
```json
{
  "host": "crash-pings.mozilla.org",
  "rootDomain": "mozilla.org",
  "severity": "medium",
  "findings": [
    {
      "type": "certificate_expiring",
      "severity": "medium",
      "detail": "Certificate expires in 21 days (2026-11-16T10:07:59+00:00)."
    }
  ],
  "findingTypes": ["certificate_expiring"],
  "cnameChain": ["mozilla-it.netlifyglobalcdn.com"],
  "thirdPartyService": null,
  "resolvedIps": ["35.190.14.201"],
  "httpStatus": null,
  "tlsValid": true,
  "certIssuer": "Google Trust Services",
  "certExpiresAt": "2026-11-16T10:07:59+00:00",
  "certDaysLeft": 21,
  "checkedAt": "2026-10-26T12:36:51.690890+00:00"
}
```

## Integrations
**Python**
```python
from apify_client import ApifyClient
client = ApifyClient("<APIFY_TOKEN>")
run = client.actor("USERNAME/subdomain-takeover-cert-expiry-radar").call(run_input={"domains": ["example.com"], "onlyRisks": True})
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item["host"], item["severity"], item["findingTypes"])
```

**Node.js**
```javascript
import { ApifyClient } from 'apify-client';
const client = new ApifyClient({ token: '<APIFY_TOKEN>' });
const run = await client.actor('USERNAME/subdomain-takeover-cert-expiry-radar').call({ domains: ['example.com'], onlyRisks: true });
const { items } = await client.dataset(run.defaultDatasetId).listItems();
console.log(items);
```

**cURL**
```bash
curl -X POST "https://api.apify.com/v2/acts/USERNAME~subdomain-takeover-cert-expiry-radar/run-sync-get-dataset-items?token=<APIFY_TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{"domains": ["example.com"], "onlyRisks": true}'
```

**MCP / AI agents**: add this Actor through the Apify MCP server (`https://mcp.apify.com?actors=USERNAME/subdomain-takeover-cert-expiry-radar`). Prompt: "Use the radar to list risky subdomains of example.com with certificates expiring in 14 days." Schedule it daily with `onlyRisks: true` and connect a webhook to Slack.

## Notes and limits
- Subdomains come from Certificate Transparency (Cert Spotter, merged with crt.sh). Hosts that never had a public certificate are not discovered.
- Takeover detection needs both a known-provider CNAME and that provider's unclaimed-resource page; unknown providers are reported only as dangling CNAMEs.
- Severity: `critical` = confirmed takeover or expired certificate, `high` = dangling CNAME or invalid certificate or expiry within 7 days, `medium` = expiry inside the warning window, `info` = healthy.
- Only audit domains you own or are authorised to test.

## Run and verify locally
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

apify validate-schema          # validates INPUT_SCHEMA.json and dataset_schema.json
python -m pytest               # 28 offline tests, no network needed

apify run --purge              # live run with the default input
ls storage/datasets/default | wc -l    # expect ~40 records for mozilla.org

# simulate pay-per-event billing locally and inspect what was charged
ACTOR_TEST_PAY_PER_EVENT=true apify run
ls storage/datasets/charging_log
```

## Deploy
```bash
apify login
apify push
```
Then in Apify Console open **Publication > Monetization**, choose **Pay per event** and add the two events from `.actor/pay_per_event.json` (`host-audited` $0.01, `risk-finding` $0.12). Publish, then schedule the Actor daily with `onlyRisks: true` and a webhook to Slack for new findings.
