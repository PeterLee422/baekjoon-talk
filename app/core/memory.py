# app/core/memory.py

import os, psutil

def print_memory_usage():
    process = psutil.Process(os.getpid())
    mem_bytes = process.memory_info().rss
    mem_mb = mem_bytes / 1024 / 1024
    print(f"[Memory] RSS: {mem_mb: .2f} MB")