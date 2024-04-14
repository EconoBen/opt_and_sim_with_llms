.ONESHELL:
.DELETE_ON_ERROR:

SHELL := /bin/bash

.PHONY: run


run:
	export PYTHONPATH=. && streamlit run src/main.py
