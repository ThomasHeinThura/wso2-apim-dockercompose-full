#!/bin/bash
set -euo pipefail
for db in shared_db apim_db; do
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres -c "CREATE DATABASE $db OWNER wso2;"
done
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname shared_db -f /schemas/shared.sql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname apim_db -f /schemas/apim.sql
