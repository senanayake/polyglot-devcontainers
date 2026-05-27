#!/usr/bin/env bash
set -euo pipefail

workspace="$(mktemp -d)"
trap 'rm -rf "${workspace}"' EXIT

sat_file="${workspace}/sat.smt2"
unsat_file="${workspace}/unsat.smt2"

cat > "${sat_file}" <<'EOF'
(set-logic QF_LIA)
(declare-const x Int)
(assert (> x 4))
(assert (< x 6))
(check-sat)
EOF

cat > "${unsat_file}" <<'EOF'
(set-logic QF_LIA)
(declare-const x Int)
(assert (> x 4))
(assert (< x 4))
(check-sat)
EOF

for solver in z3 cvc5; do
  sat_result="$("${solver}" "${sat_file}" | head -n 1 | tr -d '\r')"
  unsat_result="$("${solver}" "${unsat_file}" | head -n 1 | tr -d '\r')"

  if [[ "${sat_result}" != "sat" ]]; then
    echo "${solver}: expected sat, got ${sat_result}" >&2
    exit 1
  fi

  if [[ "${unsat_result}" != "unsat" ]]; then
    echo "${solver}: expected unsat, got ${unsat_result}" >&2
    exit 1
  fi
done

echo "smt-smoke: z3 and cvc5 verified"

