#!/bin/sh

uvicorn main:app --reload --workers 1 --host 0.0.0.0 --port 80
