#!/bin/sh
# Refuses if a tracked/stageable file looks like it holds credentials. Installed as the git pre-commit hook.
cd "$(git rev-parse --show-toplevel)"
files=$(git ls-files -co --exclude-standard)
bad=$(echo "$files" | grep -E '(^|/)\.env($|\.)|\.har$|discovery.*\.json$|\.pem$|secrets?\.(ya?ml|json)$' || true)
# a literal quoted value assigned to a password/token/secret, or an env-style KEY_PASSWORD=value line
hits=$(echo "$files" | grep -v 'tools/check_no_secrets.sh' | xargs grep -InE "(password|passwd|token|secret|api_?key)['\"]?[[:space:]]*[=:][[:space:]]*['\"][^'\"[:space:]]{4,}['\"]|^[A-Z_]*(PASSWORD|TOKEN|SECRET)=[^.<[:space:]\$][^[:space:]]*" 2>/dev/null | grep -viE 'yourpassword|example|placeholder|"password": *"password"' || true)
if [ -n "$bad$hits" ]; then echo "Possible secrets in the repo:"; echo "$bad"; echo "$hits"; exit 1; fi
echo "no secrets found"
