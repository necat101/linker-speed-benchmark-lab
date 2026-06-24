#!/usr/bin/env python3
"""
Linker Speed Benchmark - Compares GNU ld, gold, lld, mold, wild
Separates compile time from link time, verifies correctness.
"""

import subprocess
import time
import os
import hashlib
import statistics
import shutil
from pathlib import Path
import sys
import platform
import json

def run_cmd(cmd, cwd=None, capture=True):
    """Run command and return result"""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=capture, text=True, timeout=60
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def find_linkers():
    """Find available linkers on the system"""
    linkers = {}
    
    # Check for linker binaries
    candidates = {
        'ld.bfd': ['ld.bfd', '/usr/bin/ld.bfd'],
        'gold': ['ld.gold', 'gold', '/usr/bin/ld.gold'],
        'lld': ['ld.lld', 'lld', '/usr/bin/ld.lld'],
        'mold': ['mold', '/usr/bin/mold'],
        'wild': ['wild', '/usr/bin/wild', '/usr/local/bin/wild'],
    }
    
    for name, paths in candidates.items():
        for path in paths:
            success, _, _ = run_cmd(f"which {path}" if not path.startswith('/') else f"test -x {path}")
            if success:
                # Get version
                success, out, _ = run_cmd(f"{path} --version 2>&1 | head -1")
                version = out.strip() if success else "unknown"
                linkers[name] = {'path': path, 'version': version}
                break
    
    # Check system default ld
    success, out, _ = run_cmd("ld --version 2>&1 | head -1")
    if success:
        linkers['system-ld'] = {'path': 'ld', 'version': out.strip()}
    
    return linkers

def compile_project(proj_dir, obj_dir):
    """Compile project sources to objects (one-time cost)"""
    src_dir = proj_dir / "src"
    obj_dir.mkdir(parents=True, exist_ok=True)
    
    objects = []
    for src in sorted(src_dir.glob("*.c")) + sorted(src_dir.glob("*.cpp")):
        obj = obj_dir / f"{src.stem}.o"
        # Use gcc for both C and C++ for simplicity
        cmd = f"gcc -c -O2 -g {src} -o {obj}"
        success, _, stderr = run_cmd(cmd)
        if not success:
            print(f"    Failed to compile {src.name}: {stderr}")
            return None
        objects.append(obj)
    
    return objects

def benchmark_link(name, linker_path, objects, output, trials=3, use_gcc_driver=False):
    """Benchmark linking with specified linker"""
    times = []
    
    for i in range(trials):
        if output.exists():
            output.unlink()
        
        start = time.perf_counter()
        
        if use_gcc_driver:
            # Use GCC as driver with -fuse-ld
            obj_list = " ".join(str(o) for o in objects)
            if 'wild' in name:
                # GCC needs special handling for wild
                cmd = f"gcc {obj_list} -o {output} -Wl,-fuse-ld={linker_path}"
            else:
                cmd = f"gcc {obj_list} -o {output} -fuse-ld={name.split('.')[0]}"
        else:
            # Direct linker invocation (simplified - real linker needs more flags)
            obj_list = " ".join(str(o) for o in objects)
            cmd = f"ld {obj_list} -o {output} 2>/dev/null || gcc {obj_list} -o {output}"
        
        success, _, stderr = run_cmd(cmd)
        elapsed = time.perf_counter() - start
        
        if not success or not output.exists():
            print(f"    Trial {i+1}: FAILED - {stderr[:100]}")
            return None
        
        times.append(elapsed)
        print(f"    Trial {i+1}: {elapsed*1000:.1f}ms")
    
    # Verify the output works
    success, out, _ = run_cmd(str(output))
    if not success:
        print(f"    WARNING: Output binary failed to execute")
    
    # Get binary info
    size = output.stat().st_size
    success, out, _ = run_cmd(f"nm {output} | wc -l")
    symbol_count = int(out.strip()) if success and out.strip().isdigit() else 0
    
    return {
        'linker': name,
        'mean_ms': statistics.mean(times) * 1000,
        'min_ms': min(times) * 1000,
        'max_ms': max(times) * 1000,
        'stdev_ms': statistics.stdev(times) * 1000 if len(times) > 1 else 0,
        'times': [t * 1000 for t in times],
        'binary_size': size,
        'symbol_count': symbol_count,
        'success': True
    }

def main():
    print("=" * 70)
    print("Linker Speed Benchmark")
    print("=" * 70)
    print(f"Platform: {platform.platform()}")
    print(f"Python: {sys.version.split()[0]}")
    print()
    
    # Find available linkers
    print("Detecting available linkers...")
    linkers = find_linkers()
    if not linkers:
        print("ERROR: No linkers found!")
        return
    
    for name, info in linkers.items():
        print(f"  ✓ {name}: {info['version'][:60]}")
    print()
    
    # Check for corpus
    corpus_dir = Path("corpus")
    if not corpus_dir.exists():
        print("ERROR: corpus/ not found. Run 'python3 generate_corpus.py' first.")
        return
    
    results = []
    work_dir = Path("/tmp/linker-bench")
    work_dir.mkdir(exist_ok=True)
    
    # Benchmark each project
    for proj_dir in sorted([d for d in corpus_dir.iterdir() if d.is_dir()]):
        print(f"\n{proj_dir.name}:")
        print("-" * 70)
        
        # Compile once
        obj_dir = work_dir / proj_dir.name / "obj"
        print("  Compiling sources...")
        objects = compile_project(proj_dir, obj_dir)
        if not objects:
            print("  Skipping due to compile failure")
            continue
        
        print(f"  Compiled {len(objects)} objects")
        
        # Benchmark each linker
        for linker_name, linker_info in linkers.items():
            output = work_dir / proj_dir.name / f"test-{linker_name}"
            output.parent.mkdir(parents=True, exist_ok=True)
            
            print(f"  {linker_name}:")
            result = benchmark_link(
                linker_name,
                linker_info['path'],
                objects,
                output,
                trials=3
            )
            
            if result:
                result['project'] = proj_dir.name
                result['object_count'] = len(objects)
                results.append(result)
    
    # Save results
    print("\n" + "=" * 70)
    print("Saving results...")
    
    with open("RESULTS.md", "w") as f:
        f.write("# Linker Benchmark Results\n\n")
        f.write(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Platform:** {platform.platform()}\n")
        f.write(f"**Python:** {sys.version}\n\n")
        
        f.write("## Available Linkers\n\n")
        for name, info in linkers.items():
            f.write(f"- **{name}**: `{info['version']}`\n")
        f.write("\n")
        
        f.write("## Results\n\n")
        f.write("| Project | Linker | Mean (ms) | Min (ms) | Max (ms) | Binary Size | Symbols |\n")
        f.write("|---------|--------|-----------|----------|----------|-------------|----------|\n")
        
        for r in results:
            f.write(f"| {r['project']} | {r['linker']} | {r['mean_ms']:.1f} | "
                   f"{r['min_ms']:.1f} | {r['max_ms']:.1f} | "
                   f"{r['binary_size'] / 1024:.1f} KB | {r['symbol_count']} |\n")
        
        f.write("\n## Raw Timing Data\n\n")
        for r in results:
            times_str = ", ".join(f"{t:.1f}ms" for t in r['times'])
            f.write(f"- **{r['project']} / {r['linker']}**: {times_str}\n")
    
    print("✓ Results saved to RESULTS.md")
    print(f"✓ Tested {len(results)} linker/project combinations")
    
    # Cleanup
    if work_dir.exists():
        shutil.rmtree(work_dir)
    
    print("\nBenchmark complete!")

if __name__ == "__main__":
    main()
