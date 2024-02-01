bundle:
    redocly bundle openapi.json -o nba_stats_api.json --force

run:
    poetry run python3 nba_stats_generator/generate_parameters.py

build-docs:
    redocly build-docs nba_stats_api.json