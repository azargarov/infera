#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

python3 -m unittest discover -s tests -p 'test_*.py'
python3 validation/validate_scenario.py scenarios/*.yaml
python3 validation/validate_knowledge.py \
  knowledge/system/*.yaml knowledge/components/*.yaml knowledge/patterns/*.yaml \
  --scenario-id healthy-001 \
  --scenario-id ambiguous-001 \
  --scenario-id service-failure-001 \
  --scenario-id resource-pressure-001 \
  --scenario-id storage-001 \
  --scenario-id network-dependency-001 \
  --scenario-id pm-restart-001

tmp_examples=$(mktemp -d)
trap 'rm -rf "$tmp_examples"' EXIT
for run_dir in examples/runs/*; do
  [[ -d "$run_dir" ]] || continue
  check_dir="$tmp_examples/$(basename "$run_dir")"
  cp -a "$run_dir" "$check_dir"
  python3 validation/validate_run.py "$check_dir"
  case "$(basename "$run_dir")" in
    service-failure-001) python3 validation/evaluate_service_failure.py "$check_dir" >/dev/null ;;
    ambiguous-001) python3 validation/evaluate_ambiguous.py "$check_dir" >/dev/null ;;
    resource-pressure-001) python3 validation/evaluate_resource_pressure.py "$check_dir" >/dev/null ;;
    storage-001) python3 validation/evaluate_storage.py "$check_dir" >/dev/null ;;
    network-dependency-001) python3 validation/evaluate_network_dependency.py "$check_dir" >/dev/null ;;
    pm-restart-001-dry-run|pm-restart-001-approved) python3 validation/evaluate_pm_restart.py "$check_dir" >/dev/null ;;
  esac
done

python3 -m compileall -q validation tests
python3 - <<'PY'
from pathlib import Path
import yaml
for path in Path('.').rglob('*.yaml'):
    if '.git' not in path.parts and '__pycache__' not in path.parts:
        yaml.safe_load(path.read_text(encoding='utf-8'))
print('YAML PARSE CHECK PASSED')
PY

mapfile -t shell_files < <(find lab validation -type f -name '*.sh' -print)
if ((${#shell_files[@]})); then bash -n "${shell_files[@]}"; fi
python3 validation/check_public_boundary.py
if git ls-files | grep -E '(^|/)(overlay\.qcow2|seed\.iso|id_ed25519(\.pub)?|known_hosts|serial\.log)$'; then
  echo 'tracked runtime artifact found' >&2
  exit 1
fi
git diff --check
echo 'LOCAL CI CHECK PASSED'
