import pathlib
import json
import re

from typing import Any

IGNORED_ENDPOINTS = (
    "LeagueDashPlayerShotLocations",
    "LeagueDashTeamShotLocations",
    "PlayerIndex",
)

# https://github.com/sportsdataverse/wehoop/blob/f59622bc1fe29dc5130719b2602391faaf7bfeaf/R/utils_wnba_stats.R#L103
WNBA_ENDPOINTS = (
    "alltimeleadersgrids",
    "assistleaders",
    "assisttracker",
    "boxscoreadvancedv2",
    "boxscoredefensive",
    "boxscorefourfactorsv2",
    "boxscorematchups",
    "boxscoremiscv2",
    "boxscoreplayertrackv2",
    "boxscorescoringv2",
    "boxscoresimilarityscore",
    "boxscoresummaryv2",
    "boxscoretraditionalv2",
    "boxscoreusagev2",
    "commonallplayers",
    "commonplayerinfo",
    "commonplayoffseries",
    "commonteamroster",
    "commonteamyears",
    "cumestatsplayer",
    "cumestatsplayergames",
    "cumestatsteam",
    "cumestatsteamgames",
    "defensehub",
    "draftboard",
    "draftcombinedrillresults",
    "draftcombinenonstationaryshooting",
    "draftcombineplayeranthro",
    "draftcombinespotshooting",
    "draftcombinestats",
    "drafthistory",
    "fantasywidget",
    "franchisehistory",
    "franchiseleaders",
    "franchiseplayers",
    "gamerotation",
    "glalumboxscoresimilarityscore",
    "homepageleaders",
    "homepagev2",
    "infographicfanduelplayer",
    "leaderstiles",
    "leaguedashlineups",
    "leaguedashplayerbiostats",
    "leaguedashplayerclutch",
    "leaguedashplayerptshot",
    "leaguedashplayershotlocations",
    "leaguedashplayerstats",
    "leaguedashptdefend",
    "leaguedashptstats",
    "leaguedashptteamdefend",
    "leaguedashteamclutch",
    "leaguedashoppptshot",
    "leaguedashteamptshot",
    "leaguedashteamshotlocations",
    "leaguedashteamstats",
    "leaguegamefinder",
    "leaguegamelog",
    "leagueleaders",
    "leaguelineupviz",
    "leagueplayerondetails",
    "leagueseasonmatchups",
    "leaguestandings",
    "leaguestandingsv3",
    "matchupsrollup",
    "playbyplay",
    "playbyplayv2",
    "playerawards",
    "playercareerbycollege",
    "playercareerbycollegerollup",
    "playercareerstats",
    "playercompare",
    "playerdashptpass",
    "playerdashptreb",
    "playerdashptshotdefend",
    "playerdashptshots",
    "playerdashboardbyclutch",
    "playerdashboardbygamesplits",
    "playerdashboardbygeneralsplits",
    "playerdashboardbylastngames",
    "playerdashboardbyopponent",
    "playerdashboardbyshootingsplits",
    "playerdashboardbyteamperformance",
    "playerdashboardbyyearoveryear",
    "playerestimatedmetrics",
    "playerfantasyprofile",
    "playerfantasyprofilebargraph",
    "playergamelog",
    "playergamelogs",
    "playergamestreakfinder",
    "playernextngames",
    "playerprofilev2",
    "playervsplayer",
    "playoffpicture",
    "scoreboard",
    "scoreboardv2",
    "shotchartdetail",
    "shotchartleaguewide",
    "shotchartlineupdetail",
    "synergyplaytypes",
    "teamandplayersvsplayers",
    "teamdashlineups",
    "teamdashptpass",
    "teamdashptreb",
    "teamdashptshots",
    "teamdashboardbyclutch",
    "teamdashboardbygamesplits",
    "teamdashboardbygeneralsplits",
    "teamdashboardbylastngames",
    "teamdashboardbyopponent",
    "teamdashboardbyshootingsplits",
    "teamdashboardbyteamperformance",
    "teamdashboardbyyearoveryear",
    "teamdetails",
    "teamestimatedmetrics",
    "teamgamelog",
    "teamgamelogs",
    "teamgamestreakfinder",
    "teamhistoricalleaders",
    "teaminfocommon",
    "teamplayerdashboard",
    "teamplayeronoffdetails",
    "teamplayeronoffsummary",
    "teamvsplayer",
    "teamyearbyyearstats",
    "videodetails",
    "videoevents",
    "videostatus",
    "winprobabilitypbp",
)


def generate_parameters(dir: pathlib.Path) -> None:
    with (dir / "analysis.json").open("r") as analysis_file:
        analysis: dict[str, Any] = json.load(analysis_file)

    openapi_file_path = dir / "openapi.json"
    specification_dir = dir / "specification"

    parameter_dir = specification_dir / "parameters"
    if not parameter_dir.exists():
        parameter_dir.mkdir()

    path_dir = specification_dir / "paths"
    if not path_dir.exists():
        path_dir.mkdir()

    schema_dir = specification_dir / "schemas"
    if not schema_dir.exists():
        schema_dir.mkdir()

    data_set_dir = specification_dir / "data_sets"
    if not data_set_dir.exists():
        data_set_dir.mkdir()

    with (dir / "specification" / "frontmatter.json").open("r") as frontmatter_file:
        openapi: dict[str, Any] = json.load(frontmatter_file)

    parameters: set[str] = set()
    data_sets: set[str] = set()
    schemas: set[str] = set()
    openapi["paths"] = {}
    for endpoint, endpoint_vals in analysis.items():
        if endpoint_vals["status"] in ["deprecated", "invalid"]:
            continue

        if endpoint in IGNORED_ENDPOINTS:
            continue

        openapi["paths"][f"/{endpoint.lower()}"] = {
            "$ref": f"specification/paths/{endpoint}.json"
        }
        temp_path: dict[str, Any] = {
            "get": {
                "summary": endpoint,
                "operationId": endpoint,
                "description": "[to do]",
                "security": [],
                "tags": ["nba"],
                "parameters": [],
                "responses": {
                    "200": {
                        "description": "[to do]",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "parameters": {
                                            "type": "object",
                                            "properties": {},
                                        },
                                        "resource": {"const": endpoint.lower()},
                                        "resultSets": {
                                            "type": "array",
                                            "prefixItems": [],
                                        },
                                    },
                                }
                            },
                        },
                    },
                    "404": {"description": "[to do]"},
                },
            }
        }
        if endpoint.lower() in WNBA_ENDPOINTS:
            temp_path["get"]["tags"].append("wnba")
        for parameter in endpoint_vals["parameters"]:
            temp_path["get"]["parameters"].append(
                {"$ref": f"../parameters/{parameter}.json"}
            )

            # temp_path["get"]["responses"]["200"]["content"]["application/json"][
            #     "schema"
            # ]["properties"]["parameters"]["properties"][parameter] = {
            #     "$ref": f"../schemas/{parameter}.json"
            # }

            temp_path["get"]["responses"]["200"]["content"]["application/json"][
                "schema"
            ]["properties"]["parameters"]["properties"][parameter] = {
                "const": f"$request.query.{parameter}"
            }

            if parameter in parameters:
                continue
            else:
                parameters.add(parameter)

            temp_param: dict[str, Any] = {
                "name": parameter,
                "description": "[to do]",
                "in": "query",
                "schema": {"$ref": f"../schemas/{parameter}.json"},
            }
            if parameter in endpoint_vals["required_parameters"]:
                temp_param["required"] = True
            with (parameter_dir / f"{parameter}.json").open("w") as param_file:
                json.dump(temp_param, param_file, indent=2)

            schema = parameter
            if schema in schemas:
                continue
            else:
                schemas.add(schema)

            temp_schema: dict[str, Any] = {"description": "[to do]"}
            if schema in endpoint_vals["nullable_parameters"]:
                temp_schema["type"] = ["null", "string"]
                nullable = True
            else:
                temp_schema["type"] = "string"
                nullable = False

            if (pattern := endpoint_vals["parameter_patterns"].get(schema)) is not None:
                if "{" in pattern:  # probably regex. probably.
                    temp_schema["pattern"] = pattern
                else:
                    temp_schema["enum"] = [
                        re.sub(r"[^a-zA-Z0-9\s\-]+", "", option)
                        for option in pattern.split("|")
                    ]
                    if nullable:
                        temp_schema["enum"].insert(0, None)

            with (schema_dir / f"{schema}.json").open("w") as schema_file:
                json.dump(temp_schema, schema_file, indent=2)

        temp_data_sets = endpoint_vals["data_sets"]
        temp_path["get"]["responses"]["200"]["content"]["application/json"]["schema"][
            "properties"
        ]["resultSets"]["prefixItems"] = [
            {"$ref": f"../data_sets/{data_set}.json"} for data_set in temp_data_sets
        ]

        temp_path["get"]["responses"]["200"]["content"]["application/json"]["schema"][
            "properties"
        ]["resultSets"]["minItems"] = len(temp_data_sets)
        temp_path["get"]["responses"]["200"]["content"]["application/json"]["schema"][
            "properties"
        ]["resultSets"]["maxItems"] = len(temp_data_sets)

        with (path_dir / f"{endpoint}.json").open("w") as path_file:
            json.dump(temp_path, path_file, indent=2)

    print("\n")

    for endpoint, endpoint_vals in analysis.items():
        if endpoint_vals["status"] in ["deprecated", "invalid"]:
            continue
        print(endpoint)

        if endpoint in IGNORED_ENDPOINTS:
            continue

        for data_set, data_set_vals in endpoint_vals["data_sets"].items():
            if data_set in data_sets:
                continue
            else:
                data_sets.add(data_set)

            temp_data_set: dict[str, Any] = {
                "type": "object",
                "properties": {
                    "name": {"const": data_set},
                    #"x-tags": ["dataset"],
                    "headers": {
                        "type": "array",
                        "prefixItems": [
                            {"const": data_set_val} for data_set_val in data_set_vals
                        ],
                        "minItems": len(data_set_vals),
                        "maxItems": len(data_set_vals),
                    },
                    "rowSet": {
                        "type": "array",
                        "items": {"type": "array", "prefixItems": []},
                    },
                },
            }

            count: int = 0
            for column_val in data_set_vals:
                cleaned_column_val = "".join(
                    [val.capitalize() for val in column_val.split("_")]
                )

                temp_data_set["properties"]["rowSet"]["items"]["prefixItems"].append(
                    {"$ref": f"../schemas/{cleaned_column_val}.json"}
                )
                count += 1

                if cleaned_column_val in schemas:
                    continue
                else:
                    schemas.add(cleaned_column_val)

                with (schema_dir / f"{cleaned_column_val}.json").open(
                    "w"
                ) as schema_file:
                    json.dump(
                        {"description": "[to do]", "type": "string"},
                        schema_file,
                        indent=2,
                    )
            temp_data_set["properties"]["rowSet"]["items"]["minItems"] = count
            temp_data_set["properties"]["rowSet"]["items"]["maxItems"] = count

            with (data_set_dir / f"{data_set}.json").open("w") as data_set_file:
                json.dump(temp_data_set, data_set_file, indent=2)

    for openapi_dir, items in {schema_dir: schemas, parameter_dir: parameters}.items():
        with (openapi_dir / "_index.json").open("w") as index_schema_file:
            json.dump(
                {item: {"$ref": f"./{item}.json"} for item in sorted(items)},
                index_schema_file,
                indent=2,
            )

    openapi.update(
        {
            "components": {
                "parameters": {"$ref": "specification/parameters/_index.json"},
                "schemas": {"$ref": "specification/schemas/_index.json"},
            },
            "tags": [
                {
                    "name": "nba",
                    "description": "Endpoints available in the NBA stats website",
                },
                {
                    "name": "wnba",
                    "description": "Endpoints available only in the WNBA stats website",
                },
            ],
        }
    )

    with openapi_file_path.open("w") as openapi_file:
        json.dump(openapi, openapi_file, indent=2)

    return


if __name__ == "__main__":
    working_dir = pathlib.Path(__file__).resolve().parents[1]
    generate_parameters(working_dir)
