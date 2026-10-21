# TOML for ris

A TOML 0.5.0 parser ported from `iyis/toml`, originally
[crystal-community/toml.cr 0.8.1](https://github.com/crystal-community/toml.cr).
The original Crystal source in `archive/crystal/` is unchanged; the git
history retains the original authors and the iyi port.

```ris
import toml::{TOML}

config = TOML.parse(File.read("config.toml"))
puts config["owner"]["name"].as_s
puts config["database"]["ports"][0].as_i
File.write("names.toml", "name = #{TOML.quote("say \"hi\"")}\n")
```

Use a local module checkout for now; this ris port has not been published.
`iyi.mod` supplies the module identity used by the ris toolchain.

## Memory and lifetime

`parse(String) : TOML::Table` returns an owned `Hash(String, TOML::Any)`.
Its keys, strings, nested tables and arrays remain valid after parsing.
Configuration is commonly retained, so a borrowed tree would force callers
to manage its lifetime or copy the entire tree before caching it.

Parsing opens `Tape.scope` internally. The decoded character array uses
`TapeArray(Char)`; key/string assembly uses `TapeWriter` through a private
UTF-8 writer. Only completed strings are copied into the owned result.
The lexer and parser are `@[OnTape]` structs, so the compiler checks their
scratch-data lifetime. The token and returned tree use ordinary memory.
There is no intermediate heap tree that gets copied onto tape.

`quote(String) : String` also uses a scoped tape writer and returns an
independent string. No caller scope, conversion, or tape/heap API suffix is
needed. Called inside another `Tape.scope`, these methods share that scope:
scratch allocations are reclaimed when the outermost scope ends. Repeated
parsing in a long outer scope therefore accumulates scratch memory.

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
