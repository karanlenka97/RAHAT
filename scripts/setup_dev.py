#!/usr/bin/env python3
"""RAHAT Development Environment Setup & Health Verification Script."""
import sys
import subprocess
import shutil

def check_command(cmd_name: str) -> bool:
    found = shutil.which(cmd_name) is not None
    print(f"[{'OK' if found else 'MISSING'}] Tool: {cmd_name}")
    return found

def main():
    print("========================================")
    print("RAHAT / SwasthyaSetu Dev Environment Check")
    print("========================================")
    tools = ["node", "npm", "py", "python", "docker", "git"]
    for tool in tools:
        check_command(tool)
    print("========================================")

if __name__ == "__main__":
    main()
