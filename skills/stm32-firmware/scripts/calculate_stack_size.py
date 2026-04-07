#!/usr/bin/env python3
"""
Calculate worst-case stack usage for FreeRTOS tasks from MAP file.
"""

import sys
import re
from collections import defaultdict


def parse_map_file(map_file_path):
    """
    Parse ARM/GCC MAP file to extract function sizes and call graph.
    
    Returns:
        dict: Function name -> size in bytes
        dict: Function name -> list of called functions
    """
    function_sizes = {}
    call_graph = defaultdict(list)
    
    try:
        with open(map_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Extract function sizes from memory map section
        # Pattern: address size function_name
        size_pattern = r'0x[0-9a-f]+\s+0x([0-9a-f]+)\s+(\w+)'
        
        for match in re.finditer(size_pattern, content):
            size_hex = match.group(1)
            function_name = match.group(2)
            size = int(size_hex, 16)
            
            if size > 0 and not function_name.startswith('_'):
                function_sizes[function_name] = size
        
        # Basic call graph extraction (limited - needs disassembly for accuracy)
        # This is approximate and may miss some calls
        
    except FileNotFoundError:
        print(f"Error: File '{map_file_path}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing MAP file: {e}")
        sys.exit(1)
    
    return function_sizes, call_graph


def calculate_stack_usage(function_name, function_sizes, call_graph, visited=None, depth=0):
    """
    Calculate worst-case stack usage for a function.
    
    Uses simple heuristic: function frame + max of called functions
    """
    if visited is None:
        visited = set()
    
    if function_name in visited:
        # Recursive call detected
        return 0
    
    if function_name not in function_sizes:
        # Unknown function (library, etc.) - estimate
        return 32  # Conservative estimate
    
    visited.add(function_name)
    
    # Get this function's frame size
    frame_size = function_sizes[function_name]
    
    # Get called functions
    called = call_graph.get(function_name, [])
    
    if not called or depth > 10:  # Limit recursion depth
        return frame_size
    
    # Calculate max stack usage of called functions
    max_called_usage = 0
    for called_func in called:
        usage = calculate_stack_usage(called_func, function_sizes, call_graph, visited.copy(), depth + 1)
        max_called_usage = max(max_called_usage, usage)
    
    return frame_size + max_called_usage


def analyze_task_stack(map_file_path, task_function, estimate_only=False):
    """
    Analyze stack usage for a FreeRTOS task.
    """
    print(f"Analyzing stack usage for task: {task_function}")
    print(f"MAP file: {map_file_path}")
    print()
    
    function_sizes, call_graph = parse_map_file(map_file_path)
    
    if not function_sizes:
        print("Warning: No function sizes found in MAP file")
        print("Ensure MAP file is generated with appropriate compiler flags:")
        print("  GCC: -Wl,-Map=output.map")
        return
    
    print(f"Found {len(function_sizes)} functions in MAP file")
    print()
    
    # If task function found, calculate its stack usage
    if task_function in function_sizes:
        stack_usage = calculate_stack_usage(task_function, function_sizes, call_graph)
        
        # Add FreeRTOS overhead (approximate)
        freertos_overhead = 200  # Context save, etc.
        
        total_stack = stack_usage + freertos_overhead
        
        # Convert bytes to words (ARM is 4 bytes per word)
        stack_words = (total_stack + 3) // 4
        
        # Add safety margin (25%)
        recommended_words = int(stack_words * 1.25)
        
        print(f"Task function: {task_function}")
        print(f"  Function stack usage: {stack_usage} bytes")
        print(f"  FreeRTOS overhead:    ~{freertos_overhead} bytes")
        print(f"  Total estimated:      {total_stack} bytes ({stack_words} words)")
        print(f"  Recommended (25% margin): {recommended_words} words")
        print()
        print(f"Suggested task configuration:")
        print(f"  #define {task_function.upper()}_STACK_SIZE  {recommended_words}U")
        
    elif estimate_only:
        # Provide general estimates
        print("Common FreeRTOS task stack sizes:")
        print()
        print("  Minimal task (LED blink):     128-256 words (512B-1KB)")
        print("  Simple peripheral task:        256-512 words (1-2KB)")
        print("  Complex processing:            512-1024 words (2-4KB)")
        print("  sprintf/printf usage:          +256 words minimum")
        print("  Float operations:              +128 words")
        print("  Nested function calls (3-5):   +128-256 words")
        print("  Local buffers:                 +buffer size")
        print()
        print("TouchGFX GUI task:               2048-4096 words (8-16KB)")
        print("LWIP network task:               1024-2048 words (4-8KB)")
        
    else:
        print(f"Warning: Task function '{task_function}' not found in MAP file")
        print()
        print("Available functions matching 'Task' or 'vTask':")
        task_functions = [f for f in function_sizes.keys() if 'Task' in f or f.startswith('vTask')]
        for i, func in enumerate(sorted(task_functions)[:20]):
            print(f"  {func}: {function_sizes[func]} bytes")
            if i == 19 and len(task_functions) > 20:
                print(f"  ... and {len(task_functions) - 20} more")
                break
    
    print()
    print("Note: This is an estimate. Actual usage may vary due to:")
    print("  - Compiler optimizations")
    print("  - Interrupt nesting")
    print("  - Dynamic stack usage (alloca, VLAs)")
    print("  - Library function calls")
    print()
    print("Enable stack overflow checking in FreeRTOSConfig.h:")
    print("  #define configCHECK_FOR_STACK_OVERFLOW 2")


def main():
    if len(sys.argv) < 2:
        print("Usage: python calculate_stack_size.py <map_file> [task_function]")
        print()
        print("Examples:")
        print("  python calculate_stack_size.py build/output.map SensorRead_Task")
        print("  python calculate_stack_size.py build/output.map  # List all functions")
        print()
        print("Generate MAP file with GCC:")
        print("  Add to linker flags: -Wl,-Map=output.map")
        sys.exit(1)
    
    map_file = sys.argv[1]
    task_function = sys.argv[2] if len(sys.argv) > 2 else None
    
    if task_function:
        analyze_task_stack(map_file, task_function)
    else:
        analyze_task_stack(map_file, "", estimate_only=True)


if __name__ == "__main__":
    main()
