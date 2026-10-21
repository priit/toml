# TOML comparison

Run `python3 bench/run.py` with local `iyi`, `ris`, `crystal` and GNU time.
The default is 50,000 small documents and 5,000 large documents per process,
one warmup and five measured rounds. All release builds finish first;
measurements run sequentially in a deterministic shuffled order.

- `iyi-original`: the separate `iyis/toml` parser.
- `ris-control`: that same parser and heap buffers with the ris compiler.
- `ris-tape`: this port, with tape scratch and an owned result.
- `crystal-original`: the unchanged archived toml.cr 0.8.1 source.

The iyi/control copies add explicit int/float imports required by today's
compiler. No parser logic changes. The control separates compiler effects
from the port's scratch representation changes; the latter include UTF-8
writing and lexer/parser structs, so this is not a pure allocator benchmark.

Inputs are prepared before timing. Every iteration parses the input and
walks the entire resulting tree, adding key/string bytes and scalar values
to a checksum. Checksums must match across all modes, including warmups.
Workloads use strings, integers, booleans, arrays and nested tables. They
avoid known syntax/Unicode-escape differences in the archived Crystal code.
The larger input has 100 service tables. This measures parse plus traversal
of owned output, not configuration-file I/O or application throughput.

`results.json` records inputs, iteration counts, source hashes, raw samples,
stdout/stderr, exit codes, elapsed/user/system times and maximum RSS.
A failed process or checksum mismatch fails the run; failed samples remain
in the output. Compiler versions and platform are included in new runs.
Peak RSS includes the runtime and output tree, not just scratch; tape's
virtual address reservation is not the same as resident memory.

## Local result, 2026-10-16

Clean sequential run: 50,000 small / 5,000 large parses, one warmup and
three measured rounds; all 32 processes passed with matching checksums.
Elapsed-time medians in seconds:

| Implementation | Small | Large | Large peak RSS, MiB |
| --- | ---: | ---: | ---: |
| iyi original | 0.10 | 0.78 | 8.33 |
| ris heap control | 0.10 | 0.75 | 8.21 |
| ris tape scratch | 0.09 | 0.61 | 7.18 |
| Crystal original | 0.79 | 10.70 | 4.39 |

For the larger document, the tape port takes about 19% less elapsed time
than the ris heap control, and about 22% less than the original iyi port.
The small-input difference is only one GNU-time timer tick (0.01 s).
Crystal's parser is a different implementation; its result does not measure
the isolated effect of tape. These are local results, not a general speed
or memory guarantee. Exact toolchain versions are in `results.json`.

The retained binaries in the recorded temporary build directory can be
measured again with `--reuse-build DIR`. Generated sources are checked
against the current port and benchmark before reuse; rebuild after changes.
