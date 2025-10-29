#!/usr/bin/env python3
"""
Wrapper script to run seed_kpi_data.py from Docker container.
This sets up the correct paths and executes the seeding script.
"""
import sys
import os

# Set up paths
sys.path.insert(0, '/app')
os.chdir('/seed')

# Import and run the main function
from seed_kpi_data import main

if __name__ == "__main__":
    main()
