"""Subdomain Takeover & Cert Expiry Radar - Apify Actor entrypoint."""

from __future__ import annotations

import asyncio
import re
import socket
import ssl
from datetime import datetime, timezone
from typing import Any

import httpx
from apify import Actor

USER_AGENT = 'Mozilla/5.0 (compatible; TakeoverRadar/1.0; +https://apify.com)'
DOH_URL = 'https://cloudflare-dns.com/dns-query'
DOMAIN_RE = re.compile(r'^(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$')
HOST_RE = re.compile(r'^[a-z0-9]([a-z0-9.-]{0,251}[a-z0-9])?$')
SEVERITY_RANK = {'info': 0, 'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
CHARGEABLE_SEVERITIES = {'medium', 'high', 'critical'}

# (regex on the CNAME target, service, distinctive body fingerprint of an unclaimed resource).
# Providers whose unclaimed page is generic (plain "404 Not Found") are deliberately excluded:
# a false critical finding costs a customer more than a missed one.
TAKEOVER_SIGNATURES: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r'(^|\.)github\.io$'), 'GitHub Pages', "There isn't a GitHub Pages site here"),
    (re.compile(r'(^|\.)herokuapp\.com$'), 'Heroku', 'No such app'),
    (re.compile(r'(^|\.)herokudns\.com$'), 'Heroku', 'No such app'),
    (re.compile(r'(^|\.)s3[.-][a-z0-9.-]*amazonaws\.com$'), 'AWS S3', 'NoSuchBucket'),
    (re.compile(r'(^|\.)azurewebsites\.net$'), 'Azure App Service', 'Error 404 - Web app not found'),
    (re.compile(r'(^|\.)myshopify\.com$'), 'Shopify', 'Sorry, this shop is currently unavailable'),
    (re.compile(r'(^|\.)ghost\.io$'), 'Ghost', 'The thing you were looking for is no longer here'),
    (re.compile(r'(^|\.)helpjuice\.com$'), 'Helpjuice', "We could not find what you're looking for"),
    (re.compile(r'(^|\.)helpscoutdocs\.com$'), 'HelpScout', 'No settings were found for this company'),
    (re.compile(r'(^|\.)zendesk\.com$'), 'Zendesk', 'Help Center Closed'),
    (re.compile(r'(^|\.)readme\.io$'), 'Readme', 'The creators of this project are still working'),
    (re.compile(r'(^|\.)surge\.sh$'), 'Surge', 'project not found'),
    (re.compile(r'(^|\.)bitbucket\.io$'), 'Bitbucket', 'Repository not found'),
    (re.compile(r'(^|\.)pantheonsite\.io$'), 'Pantheon', 'The gods are wise'),
    (re.compile(r'(^|\.)(wordpress|wpcomstaging)\.com$'), 'WordPress.com', 'Do you want to register'),
    (re.compile(r'(^|\.)netlify\.app$'), 'Netlify', 'Not Found - Request ID'),
    (re.compile(r'(^|\.)(proxy|proxy-ssl)\.webflow\.com$'), 'Webflow', "The page you are looking for doesn't exist"),
    (re.compile(r'(^|\.)unbouncepages\.com$'), 'Unbounce', 'The requested URL was not found on this server'),
    (re.compile(r'(^|\.)tumblr\.com$'), 'Tumblr', "Whatever you were looking for doesn't currently exist"),
    (re.compile(r'(^|\.)uservoice\.com$'), 'UserVoice', 'This UserVoice subdomain is currently available'),
    (re.compile(r'(^|\.)feedpress\.me$'), 'FeedPress', 'The feed has not been found'),
]


def clean_domain(raw: str) -> str | None:
    value = raw.strip().lower()
    value = re.sub(r'^[a-z]+://', '', value)
    value = value.split('/')[0].split(':')[0].lstrip('*.').rstrip('.')
    return value if DOMAIN_RE.match(value) else None


def parse_ts(value: str) -> datetime:
    value = value.replace('Z', '+00:00')
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


class Discovery:
    """Subdomain discovery from public Certificate Transparency logs with failover."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def _get_json(self, url: str, params: dict[str, str], attempts: int = 3) -> Any:
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                response = await self.client.get(url, params=params, timeout=60)
                if response.status_code == 200:
                    return response.json()
                last_error = RuntimeError(f'HTTP {response.status_code} from {url}')
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
            await asyncio.sleep(2 * attempt)
        raise RuntimeError(f'{url} failed after {attempts} attempts: {last_error}')

    async def _certspotter(self, domain: str, max_pages: int = 3) -> set[str]:
        names: set[str] = set()
        now = datetime.now(timezone.utc)
        after: str | None = None
        for _ in range(max_pages):
            params = {'domain': domain, 'include_subdomains': 'true', 'expand': 'dns_names'}
            if after:
                params['after'] = after
            data = await self._get_json('https://api.certspotter.com/v1/issuances', params)
            for issuance in data:
                if parse_ts(issuance['not_after']) < now:
                    continue
                names.update(issuance.get('dns_names', []))
            if len(data) < 100:
                break
            after = data[-1]['id']
        return names

    async def _crtsh(self, domain: str) -> set[str]:
        data = await self._get_json('https://crt.sh/', {'q': f'%.{domain}', 'output': 'json', 'exclude': 'expired'})
        names: set[str] = set()
        for row in data:
            names.update(row.get('name_value', '').split('\n'))
        return names

    async def subdomains(self, domain: str) -> set[str]:
        names: set[str] = set()
        for source in (self._certspotter, self._crtsh):
            try:
                found = await source(domain)
            except RuntimeError as exc:
                Actor.log.warning(f'Discovery source {source.__name__} failed for {domain}: {exc}')
                continue
            Actor.log.info(f'{source.__name__} returned {len(found)} names for {domain}')
            names |= found
        hosts = {n.strip().lower().rstrip('.') for n in names}
        hosts = {h for h in hosts if not h.startswith('*') and (h == domain or h.endswith('.' + domain)) and HOST_RE.match(h)}
        hosts.add(domain)
        return hosts


async def doh_query(client: httpx.AsyncClient, name: str, rtype: str) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            response = await client.get(
                DOH_URL, params={'name': name, 'type': rtype}, headers={'accept': 'application/dns-json'}, timeout=15
            )
            if response.status_code == 200:
                return response.json()
            last_error = RuntimeError(f'DoH HTTP {response.status_code}')
        except (httpx.HTTPError, ValueError) as exc:
            last_error = exc
        await asyncio.sleep(attempt)
    raise RuntimeError(f'DNS lookup {rtype} {name} failed: {last_error}')


async def resolve_chain(client: httpx.AsyncClient, host: str) -> dict[str, Any]:
    """Follow the CNAME chain; report final status and whether any target is NXDOMAIN."""
    chain: list[str] = []
    current = host
    for _ in range(8):
        answer = await doh_query(client, current, 'CNAME')
        status = answer.get('Status')
        cnames = [a['data'].rstrip('.').lower() for a in answer.get('Answer', []) if a.get('type') == 5]
        if status == 3:
            return {'chain': chain, 'nxdomain': current, 'resolves': False}
        if not cnames:
            break
        current = cnames[-1]
        chain.extend(c for c in cnames if c not in chain)
        if len(chain) >= 8:
            break
    final_target = chain[-1] if chain else host
    a_rec = await doh_query(client, final_target, 'A')
    aaaa_rec = await doh_query(client, final_target, 'AAAA')
    ips = [x['data'] for r in (a_rec, aaaa_rec) for x in r.get('Answer', []) if x.get('type') in (1, 28)]
    nxdomain = final_target if a_rec.get('Status') == 3 else None
    return {'chain': chain, 'nxdomain': nxdomain, 'resolves': bool(ips), 'ips': ips}


DER_TIME_RE = re.compile(rb'\x17\x0d(\d{12})Z|\x18\x0f(\d{14})Z')


def not_after_from_der(der: bytes) -> datetime | None:
    """Read the certificate validity end from raw DER bytes.

    A X.509 TBSCertificate stores exactly two ASN.1 time values (notBefore, notAfter)
    in its validity block before the subject name, so the second match is notAfter.
    Only used when chain validation failed and ``ssl`` refuses to decode the peer cert.
    """
    if not der:
        return None
    matches = DER_TIME_RE.findall(der)
    if len(matches) < 2:
        return None
    utc_time, generalized_time = matches[1]
    try:
        if utc_time:
            return datetime.strptime(f'{utc_time.decode()}Z', '%y%m%d%H%M%SZ').replace(tzinfo=timezone.utc)
        return datetime.strptime(f'{generalized_time.decode()}Z', '%Y%m%d%H%M%SZ').replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _tls_probe_sync(host: str, timeout: float) -> dict[str, Any]:
    result: dict[str, Any] = {'tls_ok': False, 'tls_error': None, 'issuer': None, 'not_after': None, 'days_left': None}
    context = ssl.create_default_context()
    try:
        with socket.create_connection((host, 443), timeout=timeout) as raw:
            with context.wrap_socket(raw, server_hostname=host) as tls:
                cert = tls.getpeercert() or {}
                result['tls_ok'] = True
    except ssl.SSLCertVerificationError as exc:
        result['tls_error'] = f'{exc.verify_message}'
        result['tls_error_code'] = exc.verify_code
        # Re-probe without verification so expiry data can still be read.
        insecure = ssl.create_default_context()
        insecure.check_hostname = False
        insecure.verify_mode = ssl.CERT_NONE
        try:
            with socket.create_connection((host, 443), timeout=timeout) as raw:
                with insecure.wrap_socket(raw, server_hostname=host) as tls:
                    der = tls.getpeercert(binary_form=True)
                    result['_der'] = der
                    expires = not_after_from_der(der)
                    if expires:
                        result['not_after'] = expires.isoformat()
                        result['days_left'] = (expires - datetime.now(timezone.utc)).days
        except (OSError, ssl.SSLError):
            pass
        return result
    except (OSError, ssl.SSLError) as exc:
        result['tls_error'] = f'connect_failed: {exc.__class__.__name__}'
        result['unreachable'] = True
        return result
    if cert.get('notAfter'):
        expires = datetime.fromtimestamp(ssl.cert_time_to_seconds(cert['notAfter']), tz=timezone.utc)
        result['not_after'] = expires.isoformat()
        result['days_left'] = (expires - datetime.now(timezone.utc)).days
    issuer = dict(x[0] for x in cert.get('issuer', ()))
    result['issuer'] = issuer.get('organizationName') or issuer.get('commonName')
    return result


async def tls_probe(host: str, timeout: float) -> dict[str, Any]:
    result = await asyncio.to_thread(_tls_probe_sync, host, timeout)
    result.pop('_der', None)
    return result


async def http_fingerprint(client: httpx.AsyncClient, host: str) -> tuple[int | None, str]:
    for scheme in ('https', 'http'):
        try:
            response = await client.get(f'{scheme}://{host}/', timeout=12, follow_redirects=False)
            return response.status_code, response.text[:20000]
        except httpx.HTTPError:
            continue
    return None, ''


def match_signature(targets: list[str]) -> tuple[str, str] | None:
    for target in targets:
        for pattern, service, fingerprint in TAKEOVER_SIGNATURES:
            if pattern.search(target):
                return service, fingerprint
    return None


async def audit_host(
    client: httpx.AsyncClient, host: str, root: str, warn_days: int, probe_timeout: float
) -> dict[str, Any] | None:
    dns = await resolve_chain(client, host)
    chain: list[str] = dns['chain']
    findings: list[dict[str, str]] = []
    service: str | None = None

    signature = match_signature(chain)
    if signature:
        service = signature[0]

    if dns['nxdomain'] and chain:
        findings.append({
            'type': 'dangling_cname',
            'severity': 'critical' if signature else 'high',
            'detail': f'CNAME chain ends at non-existent name {dns["nxdomain"]}; the target can be registered by an attacker.',
        })
    elif not dns['resolves']:
        return None

    status_code: int | None = None
    if dns['resolves'] and signature and signature[1] != 'NXDOMAIN':
        status_code, body = await http_fingerprint(client, host)
        if signature[1].lower() in body.lower():
            findings.append({
                'type': 'subdomain_takeover',
                'severity': 'critical',
                'detail': f'{signature[0]} returns the unclaimed-resource page ("{signature[1]}"); the subdomain can be claimed.',
            })

    tls: dict[str, Any] = {'tls_ok': False, 'tls_error': 'not_probed'}
    if dns['resolves']:
        tls = await tls_probe(host, probe_timeout)
        if tls.get('unreachable'):
            if not findings:
                return None
        elif not tls['tls_ok']:
            days_left = tls.get('days_left')
            expired = (days_left is not None and days_left < 0) or 'expired' in str(tls['tls_error']).lower()
            detail = f'TLS validation failed: {tls["tls_error"]}.'
            if tls.get('not_after'):
                detail += f' Certificate notAfter={tls["not_after"]} ({days_left} days).'
            findings.append({
                'type': 'certificate_expired' if expired else 'invalid_certificate',
                'severity': 'critical' if expired else 'high',
                'detail': detail,
            })
        elif tls['days_left'] is not None and tls['days_left'] <= warn_days:
            findings.append({
                'type': 'certificate_expiring',
                'severity': 'high' if tls['days_left'] <= 7 else 'medium',
                'detail': f'Certificate expires in {tls["days_left"]} days ({tls["not_after"]}).',
            })

    top = max(findings, key=lambda f: SEVERITY_RANK[f['severity']])['severity'] if findings else 'info'
    return {
        'host': host,
        'rootDomain': root,
        'severity': top,
        'findings': findings,
        'findingTypes': sorted({f['type'] for f in findings}),
        'cnameChain': chain,
        'thirdPartyService': service,
        'resolvedIps': dns.get('ips', []),
        'httpStatus': status_code,
        'tlsValid': tls['tls_ok'],
        'certIssuer': tls.get('issuer'),
        'certExpiresAt': tls.get('not_after'),
        'certDaysLeft': tls.get('days_left'),
        'checkedAt': datetime.now(timezone.utc).isoformat(),
    }


async def main() -> None:
    async with Actor:
        actor_input = await Actor.get_input() or {}
        raw_domains = actor_input.get('domains') or ['mozilla.org']
        max_hosts = int(actor_input.get('maxHostsPerDomain', 40))
        warn_days = int(actor_input.get('expiryWarningDays', 30))
        concurrency = max(1, min(int(actor_input.get('concurrency', 10)), 30))
        only_risks = bool(actor_input.get('onlyRisks', False))
        probe_timeout = float(actor_input.get('probeTimeoutSecs', 8))

        domains = []
        for raw in raw_domains:
            domain = clean_domain(str(raw))
            if domain and domain not in domains:
                domains.append(domain)
            elif not domain:
                Actor.log.warning(f'Skipping invalid domain input: {raw!r}')
        if not domains:
            await Actor.fail(status_message='No valid domains supplied.')
            return

        proxy_input = actor_input.get('proxyConfiguration')
        proxy_url: str | None = None
        if proxy_input:
            try:
                proxy_config = await Actor.create_proxy_configuration(actor_proxy_input=proxy_input)
                proxy_url = await proxy_config.new_url() if proxy_config else None
            except ValueError as exc:
                Actor.log.warning(f'Proxy unavailable, continuing with direct connection: {exc}')

        limits = httpx.Limits(max_connections=concurrency * 2)
        stop = asyncio.Event()
        stats = {'audited': 0, 'findings': 0, 'errors': 0}
        semaphore = asyncio.Semaphore(concurrency)
        seen_hosts: set[str] = set()

        async with httpx.AsyncClient(
            headers={'user-agent': USER_AGENT}, proxy=proxy_url, limits=limits, verify=False
        ) as http_client, httpx.AsyncClient(headers={'user-agent': USER_AGENT}, proxy=proxy_url, limits=limits) as api_client:
            discovery = Discovery(api_client)

            async def worker(host: str, root: str) -> None:
                if stop.is_set() or host in seen_hosts:
                    return
                seen_hosts.add(host)
                async with semaphore:
                    if stop.is_set():
                        return
                    try:
                        record = await audit_host(http_client, host, root, warn_days, probe_timeout)
                    except Exception as exc:  # noqa: BLE001 - one bad host must not kill the run
                        stats['errors'] += 1
                        Actor.log.warning(f'Audit failed for {host}: {exc}')
                        return
                if record is None:
                    return
                has_risk = record['severity'] in CHARGEABLE_SEVERITIES
                if only_risks and not has_risk:
                    return
                await Actor.push_data(record)
                stats['audited'] += 1
                result = await Actor.charge('host-audited')
                if has_risk:
                    stats['findings'] += 1
                    result = await Actor.charge('risk-finding')
                if result.event_charge_limit_reached:
                    Actor.log.info('Pay-per-event charge limit reached; stopping.')
                    stop.set()

            for domain in domains:
                if stop.is_set():
                    break
                Actor.log.info(f'Discovering subdomains for {domain} via Certificate Transparency logs')
                try:
                    hosts = sorted(await discovery.subdomains(domain))
                except Exception as exc:  # noqa: BLE001
                    Actor.log.error(f'Discovery failed for {domain}: {exc}')
                    continue
                hosts = hosts[:max_hosts]
                Actor.log.info(f'Auditing {len(hosts)} hosts for {domain}')
                await asyncio.gather(*(worker(h, domain) for h in hosts))

        message = f'Audited {stats["audited"]} live hosts, {stats["findings"]} risk findings, {stats["errors"]} errors.'
        Actor.log.info(message)
        await Actor.set_status_message(message)


if __name__ == '__main__':
    asyncio.run(main())
