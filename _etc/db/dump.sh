#!/usr/bin/env bash
# Set strict error handling:
# -e: Exit immediately if a command exits with a non-zero status.
# -u: Treat unset variables as an error when substituting.
# -o pipefail: Consider errors in a pipeline as fatal.
set -euo pipefail

# Change to the directory where the script is located
cd "$(dirname "$0")"

DEV_DB="stratum_dev"
USER="admin"
DUMP_FILE="dumps/dev.dump"

# perform dump
pg_dump --dbname=$DEV_DB --host=localhost --username=$USER -Fc --no-owner --no-acl --file=$DUMP_FILE
