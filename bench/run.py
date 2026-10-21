#!/usr/bin/env python3
"""Build first, then compare the same owned TOML result in four implementations."""
import argparse
import hashlib
import json
import os
import platform
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
IYI = ROOT.parents[1] / 'iyis/toml'
BODY = '''
def digest(value : TOML::Any) : Int64
  case raw = value.raw
  when String
    total = 0_i64
    raw.each_byte { |byte| total += byte.to_i64 }
    total
  when Int64
    raw
  when Bool
    raw ? 1_i64 : 0_i64
  when Array(TOML::Any)
    total = 0_i64
    raw.each { |item| total += digest(item) }
    total
  when Hash(String, TOML::Any)
    total = 0_i64
    raw.each do |key, item|
      key.each_byte { |byte| total += byte.to_i64 }
      total += digest(item)
    end
    total
  else
    0_i64
  end
end
text = File.read(ARGV[0])
n = ARGV[1].to_i
sum = 0_i64
n.times { sum += digest(TOML::Any.new(TOML.parse(text))) }
puts sum
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--iterations', type=int, default=50000)
    ap.add_argument('--rounds', type=int, default=5)
    ap.add_argument('--reuse-build', type=Path, help='reuse binaries only after checking all generated sources')
    ap.add_argument('--output', type=Path, default=ROOT / 'bench/results.json')
    args = ap.parse_args()
    if min(args.iterations, args.rounds) < 1:
        ap.error('iterations and rounds must be positive')
    build = args.reuse_build.resolve() if args.reuse_build else Path(tempfile.mkdtemp(prefix='ris-toml-bench.'))
    def stage(path, text):
        if args.reuse_build:
            if not path.exists() or path.read_text() != text:
                raise RuntimeError('Source changed; rebuild required: ' + str(path))
        else:
            path.write_text(text)
    env = dict(os.environ, IYI_CACHE_DIR=str(build / 'cache'), CRYSTAL_CACHE_DIR=str(build / 'crystal-cache'))
    workloads = {
        'small': 'title = "Tere õ😀"\nactive = true\nports = [8000, 8001]\n[owner]\nname = "Priit"\n',
        'large': '\n'.join(f'[service.s{i}]\nname = "Service {i} õ😀"\nport = {8000+i}\nactive = true\nvalues = [1, 2, 3, 4]' for i in range(100)) + '\n',
    }
    for name, text in workloads.items():
        (build / (name + '.toml')).write_text(text)
    versions = {name: subprocess.check_output([name, '--version'], env=env, text=True).strip() for name in ('iyi', 'ris', 'crystal')}
    rows = []
    sources = {}
    for mode in ('iyi-original', 'ris-control', 'ris-tape', 'crystal-original'):
        folder = build / mode
        folder.mkdir(exist_ok=True)
        crystal = mode == 'crystal-original'
        ext = '.cr' if crystal else ('.iyi' if mode == 'iyi-original' else '.ri')
        compiler = 'crystal' if crystal else ('iyi' if mode == 'iyi-original' else 'ris')
        if crystal:
            if not args.reuse_build:
                shutil.copytree(ROOT / 'archive/crystal', folder / 'original')
            for original in (ROOT / 'archive/crystal/src').rglob('*.cr'):
                copied = folder / 'original' / original.relative_to(ROOT / 'archive/crystal')
                if copied.read_bytes() != original.read_bytes():
                    raise RuntimeError('Archived source changed; rebuild required')
            prefix = 'require "./original/src/toml"\n'
            sources[mode] = {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((folder / 'original/src').rglob('*.cr'))}
        else:
            text = (ROOT / 'toml.ri').read_text() if mode == 'ris-tape' else (IYI / 'toml.iyi').read_text()
            # Current compiler requires explicit providers; no parser logic changes.
            if mode != 'ris-tape':
                text = text.replace('import std/indexable', 'import std/int\nimport std/float\nimport std/indexable')
            stage(folder / ('toml' + ext), text)
            sources[mode] = {'toml' + ext: hashlib.sha256(text.encode()).hexdigest()}
            prefix = 'module benchmark\nimport toml::{TOML}\nimport std/text\nimport std/int\n'
        source = folder / ('main' + ext)
        stage(source, prefix + (BODY if crystal else BODY.replace('ARGV', 'Program.args')))
        binary = folder / 'main'
        if args.reuse_build:
            if not binary.is_file() or binary.stat().st_mtime < source.stat().st_mtime:
                raise RuntimeError('Missing or stale binary: ' + str(binary))
        else:
            subprocess.run([compiler, 'build', '--release', str(source), '-o', str(binary)], cwd=folder, env=env, check=True)
        for name in workloads:
            n = args.iterations if name == 'small' else max(1, args.iterations // 10)
            rows.append(dict(mode=mode, workload=name, iterations=n, binary=str(binary), input=str(build / (name + '.toml')), samples=[]))
    def measure(row):
        report = build / 'time.txt'
        result = subprocess.run(['/usr/bin/time', '-f', '%e %U %S %M', '-o', str(report), row['binary'], row['input'], str(row['iterations'])], env=env, capture_output=True, text=True)
        sample = dict(returncode=result.returncode, stdout=result.stdout.strip(), stderr=result.stderr)
        if result.returncode == 0:
            wall, user, system, rss = map(float, report.read_text().split())
            sample.update(wall_s=wall, user_s=user, system_s=system, peak_rss_kib=rss)
        return sample
    # All compilations precede warmups and measurements.
    for row in rows:
        row['warmup'] = measure(row)
    rng = random.Random(42)
    for _ in range(args.rounds):
        order = list(rows)
        rng.shuffle(order)
        for row in order:
            row['samples'].append(measure(row))
    failed = False
    for name in workloads:
        checks = set()
        for row in (r for r in rows if r['workload'] == name):
            for sample in [row['warmup'], *row['samples']]:
                failed |= sample['returncode'] != 0
                checks.add(sample['stdout'])
        failed |= len(checks) != 1
    for row in rows:
        successful = [s for s in row['samples'] if s['returncode'] == 0]
        if successful:
            row['median_wall_s'] = statistics.median(s['wall_s'] for s in successful)
            row['median_rss_kib'] = statistics.median(s['peak_rss_kib'] for s in successful)
            print(row['mode'], row['workload'], row['median_wall_s'], row['median_rss_kib'], flush=True)
    args.output.write_text(json.dumps(dict(build_dir=str(build), platform=platform.platform(), compilers=versions, sources=sources, rounds=args.rounds, workloads=workloads, rows=rows, failed=failed), indent=2) + '\n')
    if failed:
        raise SystemExit('Benchmark failed; raw failures retained in ' + str(args.output))


if __name__ == '__main__':
    main()
