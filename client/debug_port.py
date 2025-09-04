#!/usr/bin/env python3
import os

print("=== DEBUG PORT ISSUE ===")
print("Environment variables with 'LLAMA':")
for k, v in os.environ.items():
    if 'LLAMA' in k:
        print(f"  {k} = {repr(v)}")

print("\nSpecific LLAMA_STACK_PORT check:")
port = os.environ.get("LLAMA_STACK_PORT")
print(f"  Raw value: {repr(port)}")
print(f"  Type: {type(port)}")
if port:
    print(f"  Length: {len(port)}")
    print(f"  Bytes: {port.encode('utf-8')}")
    try:
        port_int = int(port)
        print(f"  As int: {port_int}")
    except Exception as e:
        print(f"  ERROR converting to int: {e}")

print("\n=== Attempting to reproduce the error ===")
try:
    from run import main
    print("About to call main()...")
    main()
except Exception as e:
    print(f"Error in main(): {e}")
    import traceback
    traceback.print_exc()
