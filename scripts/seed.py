#!/usr/bin/env python
"""CLI: python scripts/seed.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from commerceos.database.seed import seed_database

seed_database()
