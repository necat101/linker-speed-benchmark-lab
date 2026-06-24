# Linker Benchmark Results

**Generated:** 2026-06-24 23:38:32

**Platform:** Linux-6.17.0-1009-aws-x86_64-with-glibc2.39
**Python:** 3.12.3 (main, Mar 23 2026, 19:04:32) [GCC 13.3.0]

## Available Linkers

- **system-ld**: `/bin/sh: 1: ld: not found`

## Results

| Project | Linker | Mean (ms) | Min (ms) | Max (ms) | Binary Size | Symbols |
|---------|--------|-----------|----------|----------|-------------|----------|

## Raw Timing Data

*No timing data available - required tools not installed in test environment*

## Environment Notes

This benchmark was run in an environment without build tools installed. To run actual benchmarks:

```bash
# Install basic toolchain
apt-get update && apt-get install -y build-essential binutils

# Optional: Install alternative linkers
apt-get install -y lld

# For mold (requires manual build or package)
# See: https://github.com/rui314/mold

# For wild (requires Rust/cargo)
# cargo install --locked wild-linker
```

Once tools are installed, re-run:
```bash
python3 generate_corpus.py
python3 benchmark.py
```
