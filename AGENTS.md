# Working on TOML

TOML is a native ris module: a TOML 0.5.0 parser, ported from the Crystal
shard toml.cr 0.8.1. [README.md](README.md) is for using it; this page is
for changing it.

## Layout

- `toml.ri` is the whole module, in the original's order: `TOML` (with
  `TOML.parse`, `TOML.quote` and `TOML::Any`), then the private `Token`,
  `Lexer` and `Parser`. It is one file because ris refuses an import cycle,
  and `Parser` and `TOML::Any` need each other.
- `toml_test.ri` runs toml.cr's specs and every case under `spec/`.
- `archive/crystal/` is the Crystal original, kept as a reference. Do not
  change it.

## Checks

```sh
./check.sh
python3 bench/run.py
```

The checks also run retained-result, UTF-8, growth and nested-scope cases,
then build and consume exported modules. Exported methods must be typed.
`parse` and `quote` build results in the caller's destination.
Every def, loop round and block releases scratch; keep roots on their owner.
Do not change `archive/crystal/` or the separate `iyis/toml` checkout.
Benchmarks build everything before sequential, shuffled measurements and
retain failed samples. The old heap control needs an older ris compiler;
never change the separate iyi parser to make it compile on current ris.

## Rules

- A change of behaviour gets a case in `toml_test.ri`, and a line in the
  README's values and errors section when it departs from the
  original.
- Errors name the position: the lexer's and the parser's `raise` add
  `TOML: … at line:column`.
- Whatever `TOML.quote` writes, `TOML.parse` reads back unchanged.
- Follow the original's code closely where nothing needs fixing; it keeps
  the port comparable to `archive/crystal/`.
