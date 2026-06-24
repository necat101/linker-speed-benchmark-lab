#!/usr/bin/env python3
"""
Generate reproducible C/C++ corpus for linker benchmarking.
Creates small, medium, and large projects with varying characteristics.
"""

import os
import random
from pathlib import Path

# Set seed for reproducibility
random.seed(42)

def generate_c_file(path, num_functions, num_globals, with_debug_info=True):
    """Generate a C file with specified characteristics"""
    with open(path, 'w') as f:
        f.write("// Auto-generated test file\n")
        f.write("#include <stdio.h>\n#include <stdlib.h>\n\n")
        
        # Add globals
        for i in range(num_globals):
            if with_debug_info:
                f.write(f"// Global variable {i}\n")
            f.write(f"int global_var_{i} = {random.randint(0, 1000)};\n")
        f.write("\n")
        
        # Add functions
        for i in range(num_functions):
            if with_debug_info:
                f.write(f"// Function {i} - does some work\n")
            f.write(f"int func_{os.path.basename(path).replace('.', '_')}_{i}(int x) {{\n")
            f.write(f"    int result = x * {random.randint(2, 10)};\n")
            if num_globals > 0:
                f.write(f"    result += global_var_{i % num_globals};\n")
            f.write(f"    return result;\n")
            f.write("}\n\n")

def generate_cpp_file(path, num_classes, num_templates):
    """Generate a C++ file with classes and templates"""
    with open(path, 'w') as f:
        f.write("// Auto-generated C++ test file\n")
        f.write("#include <vector>\n#include <string>\n\n")
        
        # Generate templates
        for i in range(num_templates):
            f.write(f"template<typename T>\n")
            f.write(f"class TemplateClass_{i} {{\n")
            f.write(f"    T data;\n")
            f.write(f"public:\n")
            f.write(f"    TemplateClass_{i}(T d) : data(d) {{}}\n")
            f.write(f"    T get() const {{ return data; }}\n")
            f.write("};\n\n")
        
        # Generate classes
        for i in range(num_classes):
            f.write(f"class TestClass_{i} {{\n")
            f.write("private:\n")
            f.write(f"    int value_{i};\n")
            f.write("public:\n")
            f.write(f"    TestClass_{i}(int v) : value_{i}(v) {{}}\n")
            f.write(f"    int getValue() const {{ return value_{i}; }}\n")
            f.write("};\n\n")

def create_project(base_dir, name, config):
    """Create a test project with specified configuration"""
    proj_dir = base_dir / name
    proj_dir.mkdir(parents=True, exist_ok=True)
    
    src_dir = proj_dir / "src"
    src_dir.mkdir(exist_ok=True)
    
    # Generate C files
    for i in range(config['c_files']):
        path = src_dir / f"module_{i}.c"
        generate_c_file(
            path,
            num_functions=config['funcs_per_file'],
            num_globals=config['globals_per_file'],
            with_debug_info=config.get('debug_info', True)
        )
    
    # Generate C++ files if requested
    if config.get('cpp_files', 0) > 0:
        for i in range(config['cpp_files']):
            path = src_dir / f"cpp_module_{i}.cpp"
            generate_cpp_file(
                path,
                num_classes=config.get('classes_per_file', 2),
                num_templates=config.get('templates_per_file', 1)
            )
    
    # Generate main file
    main_path = src_dir / "main.c"
    with open(main_path, 'w') as f:
        f.write("// Main entry point\n")
        f.write("#include <stdio.h>\n\n")
        f.write("int main() {\n")
        f.write(f'    printf("Hello from {name}\\n");\n')
        f.write("    return 0;\n")
        f.write("}\n")
    
    # Generate Makefile
    makefile_path = proj_dir / "Makefile"
    with open(makefile_path, 'w') as f:
        f.write(f"# Makefile for {name}\n")
        f.write("CC = gcc\n")
        f.write("CFLAGS = -c -O2\n")
        f.write("SRCDIR = src\n")
        f.write("OBJDIR = obj\n")
        f.write("BINDIR = bin\n\n")
        f.write("SOURCES = $(wildcard $(SRCDIR)/*.c) $(wildcard $(SRCDIR)/*.cpp)\n")
        f.write("OBJECTS = $(SOURCES:$(SRCDIR)/%.c=$(OBJDIR)/%.o)\n")
        f.write("OBJECTS := $(OBJECTS:$(SRCDIR)/%.cpp=$(OBJDIR)/%.o)\n\n")
        f.write("all: $(BINDIR)/test\n\n")
        f.write("$(BINDIR)/test: $(OBJECTS) | $(BINDIR)\n")
        f.write("\t$(CC) $^ -o $@\n\n")
        f.write("$(OBJDIR)/%.o: $(SRCDIR)/%.c | $(OBJDIR)\n")
        f.write("\t$(CC) $(CFLAGS) $< -o $@\n\n")
        f.write("$(OBJDIR)/%.o: $(SRCDIR)/%.cpp | $(OBJDIR)\n")
        f.write("\t$(CC) $(CFLAGS) $< -o $@\n\n")
        f.write("$(OBJDIR) $(BINDIR):\n")
        f.write("\tmkdir -p $@\n\n")
        f.write("clean:\n")
        f.write("\trm -rf $(OBJDIR) $(BINDIR)\n")
    
    return proj_dir

def main():
    print("Generating linker benchmark corpus...")
    
    base_dir = Path("corpus")
    base_dir.mkdir(exist_ok=True)
    
    projects = {
        "small": {
            "c_files": 10,
            "cpp_files": 0,
            "funcs_per_file": 5,
            "globals_per_file": 2,
            "debug_info": True,
        },
        "medium": {
            "c_files": 50,
            "cpp_files": 10,
            "funcs_per_file": 10,
            "globals_per_file": 5,
            "classes_per_file": 3,
            "templates_per_file": 2,
            "debug_info": True,
        },
        "large": {
            "c_files": 200,
            "cpp_files": 50,
            "funcs_per_file": 20,
            "globals_per_file": 10,
            "classes_per_file": 5,
            "templates_per_file": 3,
            "debug_info": True,
        },
        "symbol-heavy": {
            "c_files": 20,
            "cpp_files": 0,
            "funcs_per_file": 100,  # Many symbols
            "globals_per_file": 50,
            "debug_info": False,
        },
    }
    
    for name, config in projects.items():
        print(f"  Creating {name} project...")
        proj_dir = create_project(base_dir, name, config)
        
        # Count files
        c_count = len(list((proj_dir / "src").glob("*.c")))
        cpp_count = len(list((proj_dir / "src").glob("*.cpp")))
        print(f"    {c_count} C files, {cpp_count} C++ files")
    
    print("\n✓ Corpus generated in corpus/")
    print("  Run 'python3 benchmark.py' to benchmark linkers")

if __name__ == "__main__":
    main()
