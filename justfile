bundle:
    redocly bundle openapi.json -o nba_stats_api.json --force

generate:
    poetry run python3 nba_stats_generator/generate_schema.py

build-docs:
    redocly build-docs nba_stats_api.json