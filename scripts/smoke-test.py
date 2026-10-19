#!/usr/bin/env python3
"""Check local TLS, portals, gateway routing and both PostgreSQL schemas."""
import json, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
SYSTEM_DNS = '--system-dns' in sys.argv
def request(host, path):
    result = subprocess.run(['curl', '--noproxy', '*', '--silent', '--show-error',
        '--max-time', '30', '--cacert', str(ROOT/'certs/bimats.crt'),
        *([] if SYSTEM_DNS else ['--resolve', f'{host}:443:127.0.0.1']), '--output', '-',
        '--write-out', '\n%{http_code}', f'https://{host}{path}'], capture_output=True, text=True, check=True)
    body, code = result.stdout.rsplit('\n', 1)
    return int(code), body
for path in ['/publisher/', '/devportal/', '/admin/', '/services/Version']:
    code, body = request('apim.example.com', path)
    assert code == 200, (path, code, body[:200])
    print(f'PASS https://apim.example.com{path}: {code}')
code, body = request('api.example.com', '/bimats-no-such-api')
assert code == 404 and json.loads(body).get('message') == 'Not Found', (code, body)
print(f'PASS gateway route: WSO2 returned expected {code}')
for db, table in [('shared_db', 'um_user'), ('apim_db', 'am_api')]:
    result = subprocess.run(['docker', 'compose', '-f', 'compose.yaml', '-f', 'compose.local.yaml',
       'exec', '-T', 'postgres', 'psql', '-U', 'wso2', '-d', db, '-Atc',
       f'SELECT count(*) FROM {table};'], cwd=ROOT, text=True, capture_output=True, check=True)
    print(f'PASS PostgreSQL {db}.{table}: {result.stdout.strip()} rows')
print('All smoke checks passed (system DNS; TLS certificate verified).' if SYSTEM_DNS else 'All smoke checks passed (DNS overridden to 127.0.0.1; TLS certificate verified).')
