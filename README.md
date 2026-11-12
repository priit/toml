# TOML for ris

> **Deprecated.** The ris standard library now supports TOML; use it
> instead. This module is archived and no longer maintained.

A TOML 0.5.0 parser ported from `iyis/toml`, originally
[crystal-community/toml.cr 0.8.1](https://github.com/crystal-community/toml.cr).
The original Crystal source in `archive/crystal/` is unchanged; the git
history retains the original authors and the iyi port.

```ris
import github.com/priit/toml::{TOML}

config = TOML.parse(File.read("config.toml"))
puts config["owner"]["name"].as_s
puts config["database"]["ports"][0].as_i
File.write("names.toml", "name = #{TOML.quote("say \"hi\"")}\n")
```

Add it to a project with `ris get github.com/priit/toml`.

## Memory and lifetime

`parse(String) : TOML::Table` builds its result in the caller's scope.
`quote(String) : String` grows a String there. String, Array and Hash are
tape values; there is no heap or conversion step. Every def, loop round
and block releases its scratch when it ends.

Recursive values use pooled handles, as in current `std/toml`.
`TOML::Table` is an insertion-ordered table view with `[]`, `[]?`, `[]=`,
`keys`, `each`, `size`, `empty?` and `has_key?`. Arrays returned by `as_a`
are `SlicePool::List(TOML::Any)`, with indexing, `size`, `each` and `<<`.
These replace the former concrete Hash and Array payloads because ris
refuses runtime-sized collections containing growing recursive values.
The parser's pools and text storage are built in the caller's destination;
returned strings view that storage. Keep results in that scope. Use an
explicit `copy_to(owner)` when a value must live longer.

## Values and errors

`TOML::Any.raw` holds `Bool`, `Int64`, `Float64`, `String`, `Time`, an array
or a table. `[]` / `[]?` traverse tables and arrays. `as_s`, `as_i`,
`as_i64`, `as_f`, `as_bool`, `as_a`, `as_h` and their nullable `?` forms
extract values; `kind` names their type. `quote` roundtrips through `parse`.

Invalid input panics with `TOML: … at line:column`. A task outcome can
recover from a panic; it still prints to stderr. As in the iyi port, input
is a String, there is no `parse_file` or IO overload, times use UTC, and
`Any` has no `dig`, `as_f32`, `dup` or `clone`. Local times use today's UTC
date. The inherited fixes support four-digit `\u`, eight-digit `\U`,
refuse surrogate scalars, and handle dates followed by a space and comment.
TOML syntax and error behavior are unchanged from the iyi port.

## Development

```sh
./check.sh
python3 bench/run.py
```

Checks cover the inherited parser/lexer tests, all 39 valid and 51 invalid
fixtures, retained results after tape reuse, UTF-8 boundaries, buffer growth,
nested scopes and exported-module consumers. See [AGENTS.md](AGENTS.md) and
[bench/README.md](bench/README.md). The old iyi installer CI was removed:
run the checks with a locally built ris toolchain until distribution exists.

## Thanks and license

Thanks to toml.cr's creator Ary Borenszweig and its contributors kojix2,
maiha, Will Richardson, summer-alice, Andra Antariksa, Martin Verzilli,
Brian J. Cardiff, James Taylor, Michael Fellinger, Stygmates, Tyler Gillies,
V. Elenhaupt and vjdhama. Priit Tark at domify maintains this port for now;
the original authors are welcome to take over its maintenance.

MIT, see [LICENSE](LICENSE). The archived Crystal project has no license
file of its own.
