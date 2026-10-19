#!/usr/bin/env python3
"""Prepare local secrets, TLS certificate and pinned JDBC driver without replacing existing files."""
from pathlib import Path
import hashlib, os, secrets, subprocess

ROOT = Path(__file__).resolve().parents[1]
env = ROOT / '.env'
if not env.exists():
    values = ('POSTGRES_PASSWORD=' + secrets.token_urlsafe(24) + '\n'
              'APIM_ADMIN_PASSWORD=' + secrets.token_urlsafe(18) + '\n'
              'APIM_ENCRYPTION_KEY=' + secrets.token_hex(32) + '\n')
    fd = os.open(env, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(values)
    print('Created private .env with generated credentials.')

certs = ROOT / 'certs'
certs.mkdir(exist_ok=True)
cert, key = certs / 'bimats.crt', certs / 'bimats.key'
if cert.exists() != key.exists():
    raise SystemExit('Incomplete TLS pair: restore both certs/bimats.crt and certs/bimats.key before setup.')
if not cert.exists():
    subprocess.run(['openssl', 'req', '-x509', '-nodes', '-newkey', 'rsa:3072',
        '-days', '365', '-keyout', str(key), '-out', str(cert),
        '-subj', '/CN=apim.example.com', '-addext',
        'subjectAltName=DNS:apim.example.com,DNS:api.example.com'], check=True)
    key.chmod(0o600)
    print('Created local certificate for apim.example.com and api.example.com.')

vendor = ROOT / 'vendor'
vendor.mkdir(exist_ok=True)
jar = vendor / 'postgresql-42.7.14.jar'
expected = '73914527305a40cce504b0d3d90b23caf565136912d607ae8ae7c5895512332c'
if not jar.exists():
    subprocess.run(['curl', '--fail', '--show-error', '--location',
        'https://repo.maven.apache.org/maven2/org/postgresql/postgresql/42.7.14/postgresql-42.7.14.jar',
        '--output', str(jar)], check=True)
if hashlib.sha256(jar.read_bytes()).hexdigest() != expected:
    raise SystemExit('JDBC SHA-256 mismatch: remove the invalid JAR and rerun setup.')
print('JDBC SHA-256 verified. Setup complete; existing secrets and TLS files retained.')
