#!/bin/sh
set -eu
if [ "$(id -u)" -ne 0 ]; then
  exec sudo "$0" "$@"
fi
# Remove only the old managed mapping created for this stack.
if grep -q '^127\.0\.0\.1 .*apim\.bimats\.com.*# bimats-apim local$' /etc/hosts; then
  cp -p /etc/hosts "/etc/hosts.bimats-apim.$(date +%Y%m%d%H%M%S).bak"
  hosts_tmp=$(mktemp)
  awk '!($1 == "127.0.0.1" && /apim\.bimats\.com/ && /# bimats-apim local$/)' /etc/hosts > "$hosts_tmp"
  cat "$hosts_tmp" > /etc/hosts
fi
# Append only if the exact local mapping is absent; retain unrelated host entries.
if ! awk '$1 == "127.0.0.1" { for(i=2;i<=NF;i++) if($i=="apim.example.com") found=1 } END { exit !found }' /etc/hosts; then
  printf '\n127.0.0.1 apim.example.com api.example.com # bimats-apim local\n' >> /etc/hosts
elif ! awk '$1 == "127.0.0.1" { for(i=2;i<=NF;i++) if($i=="api.example.com") found=1 } END { exit !found }' /etc/hosts; then
  printf '\n127.0.0.1 api.example.com # bimats-apim local\n' >> /etc/hosts
fi
if [ "$(uname -s)" = Darwin ]; then
  dscacheutil -flushcache
  killall -HUP mDNSResponder || true
fi
