#!/bin/sh
set -eu
cd "$(dirname "$0")"
export IYI_CACHE_DIR="${IYI_CACHE_DIR:-/tmp/ris-toml-check-cache}"
RIS="${RIS:-ris}"
export IYI_PATH="$PWD:$("$RIS" env IYI_PATH)"
"$RIS" fmt --check toml.ri toml_test.ri lifetime_test.ri
"$RIS" test
scratch=$(mktemp -d /tmp/ris-toml-check.XXXXXX)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
cat > "$scratch/producer.ri" <<'RI'
module producer
import toml_test
import lifetime_test
RI
"$RIS" build "$scratch/producer.ri" --emit-iyimod "$scratch/modules" -o "$scratch/producer"
"$RIS" build toml_test.ri --use-iyimod "$scratch/modules" -o "$scratch/corpus"
"$scratch/corpus" > "$scratch/corpus.log" 2>&1 || { cat "$scratch/corpus.log"; exit 1; }
"$RIS" build lifetime_test.ri --use-iyimod "$scratch/modules" -o "$scratch/lifetime"
"$scratch/lifetime"
echo 'PASS: corpus, retained results and exported module'
