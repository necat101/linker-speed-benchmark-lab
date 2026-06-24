# Linker Speed Benchmark Lab

Comparing GNU ld, gold, lld, mold, wild, and compiler driver modes for linking performance and correctness.

## Background: HN Discussion

This benchmark lab was created following the Hacker News discussion about [wild](https://news.ycombinator.com/item?id=42814683) - a new fast linker for Linux written in Rust.

### Key Debate Points from HN

**Why linker speed matters:**
- In iterative development (edit-compile-run loops), linking often dominates build time
- Small code changes require minimal recompilation but full relinking
- Fast linkers shave seconds off each iteration, compounding to hours saved daily

**The LTO problem:**
- Link Time Optimization (LTO) requires recompiling the entire program from LLVM-IR
- LTO time dwarfs linker time - making fast linkers irrelevant for LTO builds
- Solution: Use fast linkers for development builds, slow linkers with LTO for release builds

**Incremental linking:**
- MSVC linker has been incremental by default for decades
- No production-ready incremental linker exists on Linux
- mold explicitly rejects incremental linking as a goal
- wild's end goal IS incremental linking - Rust's "fearless concurrency" cited as enabling factor

**Workload differences:**
- Many-small-objects vs few-large-objects behave differently
- Debug info can dominate binary size and link workload
- tmpfs vs normal filesystem produces different results
- Linker scripts, if needed, add complexity and slow down fast linkers

**Fair comparison challenges:**
- Comparing linker directly vs compiler-driver invocation can be unfair
- Compiler driver adds overhead (collecting objects, CRT files, etc.)
- Different linkers support different feature sets
- "Fastest" depends on workload, flags, filesystem, and correctness requirements

## What This Lab Tests

### Linkers Compared
- **GNU ld.bfd** - Traditional BFD linker (baseline)
- **GNU gold** - Faster ELF linker from Google (where available)
- **LLVM lld** - LLVM's linker (where available)
- **mold** - Very fast modern linker (where available)
- **wild** - New Rust-based linker aiming for incremental (where available)
- **System default** - Whatever `ld` resolves to

### Test Scenarios
- Clean link (from scratch)
- Repeated relink (unchanged objects)
- Relink after touching one object
- Static library linking
- Shared library linking
- Debug info on/off
- Stripped vs unstripped
- Many small objects vs few large objects
- Symbol-heavy vs code-heavy
- PIE vs non-PIE (where supported)
- LTO vs non-LTO (where supported)

### Correctness Verification
Each linked binary is verified to:
- Execute and produce expected output
- Have correct exit code
- Have expected exported symbol count
- Have expected binary size (within tolerance)
- Have expected sections
- Have correct dynamic dependencies
- Contain build-id if requested
- Actually use the requested linker (verified via readelf)
- Preserve or strip debug info as requested
- Be functionally equivalent across linkers (same output for same inputs)

## Usage

```bash
# Generate test corpus
python3 generate_corpus.py

# Run benchmarks
python3 benchmark.py

# View results
cat RESULTS.md
```

## Requirements

- GCC or Clang
- Python 3.8+
- binutils (readelf, nm, objdump, strip)
- Optional: gold, lld, mold, wild, hyperfine

Missing tools are skipped with clear documentation rather than causing failure.

## Results Interpretation

**Do not** claim any linker "wins" globally. Results are specific to:
- Exact corpus (file counts, sizes, symbol counts)
- Compiler and flags used
- Linker versions tested
- Hardware and filesystem
- Specific metric measured (time, memory, binary size)

See RESULTS.md for the exact conditions each measurement was taken under.

## Honest Limitations

This lab tests linking performance in isolation. Real-world considerations not measured:
- Linker feature completeness (linker scripts, etc.)
- Compatibility with obscure object file features
- Long-term stability and bug rates
- Memory usage during link (partially measured)
- Interaction with debug info generation
- Distributed build scenarios

Linker choice involves trade-offs beyond raw speed. Use this data as one input among many.
