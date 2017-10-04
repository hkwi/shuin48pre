all:
	python3 kyousanto_official.py | sort | uniq > docs/kyousanto_official.csv

