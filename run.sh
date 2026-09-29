#!/bin/bash
PYTHONPATH=src python -m coverage run --source=src --branch -m pytest tests/test_rpc.py
python -m coverage report -m