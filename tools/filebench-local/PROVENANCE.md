# Local Filebench dependency

Built 2026-09-08 for iCAT varmail experiments. No global package installation and no storage workload was run during dependency preparation. `filebench -h` passed. `setarch x86_64 -R /usr/bin/true` passed as oy.

## Executable

- `/home/oy/iCAT/tools/filebench-local/install/bin/filebench`
- Version: 1.5-alpha3
- SHA256: `fd020a589ae312feae8911b7ee2e9edd1908aeb01623129146c7b3b643d16b6f`
- `ldd`: system libc, libm and loader; no unresolved libraries.
- Runtime cvar plugins: `install/share/filebench/cvars` (compiled absolute prefix; keep installation in place).

## Sources

Official release archive: https://github.com/filebench/filebench/releases/download/1.5-alpha3/filebench-1.5-alpha3.tar.gz

Archive SHA256: `2dedfc46458f5bb13e5f5a4a9f4db6263152f6186690d57653c96138610db35a`.

`apt download filebench` failed: package unavailable in current configured indexes. No apt configuration was changed. Official Debian and Ubuntu Filebench pool paths returned 404. Used official upstream source release instead.

Build-only tools downloaded over HTTPS from Ubuntu archive and extracted using dpkg-deb into local `deps/`:

- https://archive.ubuntu.com/ubuntu/pool/main/f/flex/flex_2.6.4-8.2build1_amd64.deb — local `flex.deb`, SHA256 `c5604f55827b50e3f568b4731b7799f86b147454c867be02bc141d9d8ce561ff`
- https://archive.ubuntu.com/ubuntu/pool/main/b/bison/bison_3.8.2+dfsg-1build2_amd64.deb — local `bison.deb`, SHA256 `18f487c400da3e968a44ecb3783a443641bcd14e2b080ed9ed1167f4aa2c1612`
- https://archive.ubuntu.com/ubuntu/pool/main/m/m4/m4_1.4.19-4build1_amd64.deb — local `m4.deb`, SHA256 `30ea715845a1863abd55d11e47ab91513130bf347852d4cdeae69e9d98fa795c`

These are recorded download hashes, not independently checked against signed repository metadata.

## Build

No upstream source edits. Configured out-of-tree from this directory:

```sh
./filebench-1.5-alpha3/configure --prefix=/home/oy/iCAT/tools/filebench-local/install
```

Configure completed before flex/bison became available. Initial make generated the parser but failed because lexer generation was configured as a no-op. `build.log` preserves that failed attempt. Generated lexer explicitly, then successfully rebuilt with local tools:

```sh
export PATH=/home/oy/iCAT/tools/filebench-local/deps/usr/bin:$PATH
export BISON_PKGDATADIR=/home/oy/iCAT/tools/filebench-local/deps/usr/share/bison
export M4=/home/oy/iCAT/tools/filebench-local/deps/usr/bin/m4
flex -o parser_lex.c filebench-1.5-alpha3/parser_lex.l
make -j4 LEX=flex 'YACC=bison -y' CFLAGS='-O2 -g -fcommon -Wno-error=implicit-function-declaration -Wno-error=incompatible-pointer-types'
make install
```

`build-retry.log`, `install.log`, `config.log`, and `help.txt` preserve build/help evidence. GCC compatibility flags support the old release; this does not prove benchmark correctness.

## Launch and measurement barrier

Run as oy, not root:

```sh
setarch x86_64 -R /home/oy/iCAT/tools/filebench-local/install/bin/filebench -f /absolute/workload.f
```

The release's `aslr.c` passes `0xffffffff | ADDR_NO_RANDOMIZE` to personality, which does not reliably set the intended personality; use explicit per-process setarch. No global ASLR change is required. `utils.c:fb_set_shmmax` emits a non-root warning and returns; it does not terminate execution. Host shmmax at inspection: 18446744073692774399.

After workload definitions, use:

```text
create files
system "/absolute/barrier-script"
run 60
```

The synchronous system command blocks before `proc_create()` starts workers. `fileset_createsets()` records filecreate_done, so `run` does not recreate the prepared fileset. A parent coordinator can await a ready notification, sync the filesystem, start measurement and release the barrier. Keep the Filebench process alive across preparation and run.

Important: `parser_system()` only treats `system()<0` as failure; a child command exiting nonzero does NOT prevent `run`. The coordinator must terminate Filebench/process group on preparation or measurement failure, and must never release the barrier after a failed start. Do not rely on a barrier script's nonzero exit alone.

No barrier runtime test or varmail benchmark was executed by this dependency task; the experiment owner must log and perform its smoke test.
088a270514b73cf3c09e90fac0a089b2f4f09dfd27e9096ca7a26fb219d784b3  tools/filebench-local/filebench

## 2026-09-14 fix

`fileset.c` `fileset_resolvepath`: `fb_strlcpy(s, path, MAXPATHLEN)` into a `strlen+1` buffer aborts under _FORTIFY_SOURCE ("buffer overflow detected" at "Pre-allocating directories"). Changed the size to `strlen(path)+1`. Rebuilt; hash above. Any workload with subdirectories crashed before this fix, so no earlier filebench run on this machine ever completed.
