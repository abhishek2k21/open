"""Offline tests for the radar's detection logic. No network access required."""

import asyncio
from datetime import datetime, timezone

import httpx
import pytest

from src import main as radar


def run(coro):
    return asyncio.run(coro)


async def _no_sleep(seconds: float) -> None:
    """Skip real backoff delays inside tests."""
    return None


def _transport(responses: dict) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.url.params.get('name'), request.url.params.get('type'))
        return httpx.Response(200, json=responses.get(key, {'Status': 0, 'Answer': []}))

    return httpx.MockTransport(handler)


def a_record(ip: str = '93.184.216.34') -> dict:
    return {'Status': 0, 'Answer': [{'name': 'x', 'type': 1, 'data': ip}]}


def cname(target: str) -> dict:
    return {'Status': 0, 'Answer': [{'name': 'x', 'type': 5, 'data': target}]}


def empty() -> dict:
    return {'Status': 0, 'Answer': []}


def nxdomain() -> dict:
    return {'Status': 3, 'Answer': []}


def healthy_tls(**overrides) -> dict:
    payload = {
        'tls_ok': True,
        'tls_error': None,
        'issuer': 'Test CA',
        'not_after': '2027-01-01T00:00:00+00:00',
        'days_left': 400,
    }
    payload.update(overrides)
    return payload


def patch_tls(monkeypatch, **overrides) -> None:
    async def fake_tls_probe(host: str, timeout: float) -> dict:
        return healthy_tls(**overrides)

    monkeypatch.setattr(radar, 'tls_probe', fake_tls_probe)


def audit(responses: dict, host: str = 'a.example.com', warn_days: int = 30):
    async def scenario():
        async with httpx.AsyncClient(transport=_transport(responses)) as client:
            return await radar.audit_host(client, host, 'example.com', warn_days, 1.0)

    return run(scenario())


DIRECT_DNS = {('a.example.com', 'CNAME'): empty(), ('a.example.com', 'A'): a_record()}


@pytest.mark.parametrize(
    ('raw', 'expected'),
    [
        ('example.com', 'example.com'),
        ('HTTPS://Example.COM/path?q=1', 'example.com'),
        ('*.example.com', 'example.com'),
        ('  example.com.  ', 'example.com'),
        ('example.com:8443', 'example.com'),
        ('not a domain', None),
        ('http://localhost:3000', None),
        ('', None),
    ],
)
def test_clean_domain(raw: str, expected: str | None) -> None:
    assert radar.clean_domain(raw) == expected


def test_parse_ts_accepts_zulu_suffix() -> None:
    assert radar.parse_ts('2026-11-04T23:59:59Z') == datetime(2026, 11, 4, 23, 59, 59, tzinfo=timezone.utc)


def test_match_signature_identifies_github_pages() -> None:
    assert radar.match_signature(['acme.github.io']) == ('GitHub Pages', "There isn't a GitHub Pages site here")


def test_match_signature_ignores_unknown_providers() -> None:
    assert radar.match_signature(['internal.corp.example']) is None


def test_match_signature_rejects_lookalike_domains() -> None:
    assert radar.match_signature(['evil-github.io.attacker.com']) is None
    assert radar.match_signature(['notherokuapp.com']) is None


def test_match_signature_matches_s3_website_endpoints() -> None:
    assert radar.match_signature(['bucket.s3.amazonaws.com']) == ('AWS S3', 'NoSuchBucket')
    assert radar.match_signature(['bucket.s3-website-us-east-1.amazonaws.com']) == ('AWS S3', 'NoSuchBucket')


def test_not_after_from_der_reads_second_validity_time() -> None:
    der = b'\x30\x82\x01\x00\x17\x0d250101000000Z\x17\x0d251231235959Z\x30\x00'
    assert radar.not_after_from_der(der) == datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)


def test_not_after_from_der_handles_generalized_time() -> None:
    der = b'\x17\x0d250101000000Z\x18\x0f20301231235959Z'
    assert radar.not_after_from_der(der) == datetime(2030, 12, 31, 23, 59, 59, tzinfo=timezone.utc)


def test_not_after_from_der_returns_none_without_validity() -> None:
    assert radar.not_after_from_der(b'\x30\x00') is None


def test_discovery_merges_sources_and_drops_wildcards_and_foreign_names() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if 'certspotter' in str(request.url):
            return httpx.Response(
                200,
                json=[
                    {'id': '1', 'dns_names': ['a.example.com', '*.wild.example.com'], 'not_after': '2030-01-01T00:00:00Z'},
                    {'id': '2', 'dns_names': ['expired.example.com'], 'not_after': '2001-01-01T00:00:00Z'},
                ],
            )
        return httpx.Response(200, json=[{'name_value': 'b.example.com\nc.other.com'}])

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await radar.Discovery(client).subdomains('example.com')

    assert run(scenario()) == {'example.com', 'a.example.com', 'b.example.com'}


def test_healthy_host_is_info_severity(monkeypatch) -> None:
    patch_tls(monkeypatch)
    record = audit(DIRECT_DNS)
    assert record is not None
    assert record['severity'] == 'info'
    assert record['findings'] == []
    assert record['resolvedIps'] == ['93.184.216.34']
    assert record['tlsValid'] is True


def test_unresolvable_host_is_skipped(monkeypatch) -> None:
    patch_tls(monkeypatch)
    record = audit({('a.example.com', 'CNAME'): nxdomain(), ('a.example.com', 'A'): nxdomain()})
    assert record is None


def test_transient_tls_failure_is_retried_once(monkeypatch) -> None:
    calls = {'count': 0}

    async def flaky_tls(host: str, timeout: float) -> dict:
        calls['count'] += 1
        if calls['count'] == 1:
            return {'tls_ok': False, 'tls_error': 'connect_failed: ConnectionResetError', 'unreachable': True}
        return healthy_tls(days_left=200, not_after='2027-05-01T00:00:00+00:00')

    monkeypatch.setattr(radar, 'tls_probe', flaky_tls)
    monkeypatch.setattr(radar.asyncio, 'sleep', _no_sleep)
    record = audit(DIRECT_DNS)
    assert record is not None
    assert calls['count'] == 2
    assert record['severity'] == 'info'
    assert record['tlsValid'] is True


def test_persistent_tls_failure_skips_host(monkeypatch) -> None:
    async def dead_tls(host: str, timeout: float) -> dict:
        return {'tls_ok': False, 'tls_error': 'connect_failed: ConnectionResetError', 'unreachable': True}

    monkeypatch.setattr(radar, 'tls_probe', dead_tls)
    monkeypatch.setattr(radar.asyncio, 'sleep', _no_sleep)
    assert audit(DIRECT_DNS) is None


def test_certificate_expiring_inside_seven_days_is_high(monkeypatch) -> None:
    patch_tls(monkeypatch, days_left=5, not_after='2026-10-31T00:00:00+00:00')
    record = audit(DIRECT_DNS)
    assert record is not None
    assert record['severity'] == 'high'
    assert record['findingTypes'] == ['certificate_expiring']
    assert 'expires in 5 days' in record['findings'][0]['detail']


def test_certificate_expiring_inside_window_is_medium(monkeypatch) -> None:
    patch_tls(monkeypatch, days_left=21, not_after='2026-11-16T00:00:00+00:00')
    record = audit(DIRECT_DNS)
    assert record is not None
    assert record['severity'] == 'medium'
    assert record['findingTypes'] == ['certificate_expiring']


def test_certificate_outside_window_is_not_flagged(monkeypatch) -> None:
    patch_tls(monkeypatch, days_left=45)
    record = audit(DIRECT_DNS, warn_days=30)
    assert record is not None
    assert record['findings'] == []


def test_expired_certificate_is_critical(monkeypatch) -> None:
    patch_tls(monkeypatch, tls_ok=False, tls_error='certificate has expired', days_left=-12)
    record = audit(DIRECT_DNS)
    assert record is not None
    assert record['severity'] == 'critical'
    assert record['findingTypes'] == ['certificate_expired']


def test_hostname_mismatch_is_high(monkeypatch) -> None:
    patch_tls(monkeypatch, tls_ok=False, tls_error='Hostname mismatch', days_left=90)
    record = audit(DIRECT_DNS)
    assert record is not None
    assert record['severity'] == 'high'
    assert record['findingTypes'] == ['invalid_certificate']


def test_dangling_cname_to_unknown_provider_is_high(monkeypatch) -> None:
    patch_tls(monkeypatch)
    responses = {
        ('a.example.com', 'CNAME'): cname('gone.example.net.'),
        ('gone.example.net', 'CNAME'): empty(),
        ('gone.example.net', 'A'): nxdomain(),
        ('gone.example.net', 'AAAA'): nxdomain(),
    }
    record = audit(responses)
    assert record is not None
    assert record['severity'] == 'high'
    assert record['findingTypes'] == ['dangling_cname']
    assert record['cnameChain'] == ['gone.example.net']
    assert record['thirdPartyService'] is None


def test_dangling_cname_to_known_provider_is_critical(monkeypatch) -> None:
    patch_tls(monkeypatch)
    responses = {
        ('a.example.com', 'CNAME'): cname('acme.github.io.'),
        ('acme.github.io', 'CNAME'): empty(),
        ('acme.github.io', 'A'): nxdomain(),
        ('acme.github.io', 'AAAA'): nxdomain(),
    }
    record = audit(responses)
    assert record is not None
    assert record['severity'] == 'critical'
    assert record['thirdPartyService'] == 'GitHub Pages'


def test_unclaimed_provider_page_is_critical(monkeypatch) -> None:
    patch_tls(monkeypatch)

    async def fake_fingerprint(client, host):
        return 404, "<h1>404</h1> There isn't a GitHub Pages site here."

    monkeypatch.setattr(radar, 'http_fingerprint', fake_fingerprint)
    responses = {
        ('a.example.com', 'CNAME'): cname('acme.github.io.'),
        ('acme.github.io', 'CNAME'): empty(),
        ('acme.github.io', 'A'): a_record('185.199.108.153'),
        ('acme.github.io', 'AAAA'): empty(),
    }
    record = audit(responses)
    assert record is not None
    assert record['severity'] == 'critical'
    assert 'subdomain_takeover' in record['findingTypes']
    assert record['httpStatus'] == 404


def test_provider_cname_without_fingerprint_is_not_flagged(monkeypatch) -> None:
    patch_tls(monkeypatch)

    async def fake_fingerprint(client, host):
        return 200, '<html>real application</html>'

    monkeypatch.setattr(radar, 'http_fingerprint', fake_fingerprint)
    responses = {
        ('a.example.com', 'CNAME'): cname('acme.github.io.'),
        ('acme.github.io', 'CNAME'): empty(),
        ('acme.github.io', 'A'): a_record('185.199.108.153'),
        ('acme.github.io', 'AAAA'): empty(),
    }
    record = audit(responses)
    assert record is not None
    assert record['severity'] == 'info'
    assert record['thirdPartyService'] == 'GitHub Pages'
