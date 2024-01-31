import pathlib
import json
import re

from typing import Any


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
    openapi["paths"] = {}
    for endpoint, endpoint_vals in analysis.items():
        if endpoint_vals["status"] in ["deprecated", "invalid"]:
            continue

        print(endpoint)

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
                                            "items": [],
                                        },
                                    },
                                }
                            },
                        },
                        "404": {"description": "[to do]"},
                    },
                },
            }
        }
        for parameter in endpoint_vals["parameters"]:
            temp_path["get"]["parameters"].append(
                {"$ref": f"../parameters/{parameter}.json"}
            )

            temp_path["get"]["responses"]["200"]["content"]["application/json"][
                "schema"
            ]["properties"]["parameters"]["properties"][parameter] = {
                "$ref": f"../schemas/{parameter}.json"
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

            temp_schema: dict[str, Any] = {"description": "[to do]"}
            if parameter in endpoint_vals["nullable_parameters"]:
                temp_schema["type"] = [None, "string"]
                nullable = True
            else:
                temp_schema["type"] = "string"
                nullable = False

            if (
                pattern := endpoint_vals["parameter_patterns"].get(parameter)
            ) is not None:
                if "{" in pattern:  # probably regex. probably.
                    temp_schema["pattern"] = pattern
                else:
                    temp_schema["enum"] = [
                        re.sub(r"[^a-zA-Z0-9\s\-]+", "", option)
                        for option in pattern.split("|")
                    ]
                    if nullable:
                        temp_schema["enum"].insert(0, None)

            with (schema_dir / f"{parameter}.json").open("w") as schema_file:
                json.dump(temp_schema, schema_file, indent=2)

        temp_path["get"]["responses"]["200"]["content"]["application/json"]["schema"][
            "properties"
        ]["resultSets"]["items"] = [
            {"type": {"$ref": f"../data_sets/{data_set}.json"}}
            for data_set in endpoint_vals["data_sets"]
        ]

        with (path_dir / f"{endpoint}.json").open("w") as path_file:
            json.dump(temp_path, path_file, indent=2)

    print("\n")

    for endpoint, endpoint_vals in analysis.items():
        if endpoint_vals["status"] in ["deprecated", "invalid"]:
            continue
        print(endpoint)

        if endpoint in [
            "LeagueDashPlayerShotLocations",
            "LeagueDashTeamShotLocations",
            "PlayerIndex",
        ]:
            continue

        for data_set, data_set_vals in endpoint_vals["data_sets"].items():
            if data_set in data_sets:
                continue
            else:
                data_sets.add(data_set)

            temp_data_set: dict[str, Any] = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "headers": {
                        "type": "array",
                        "items": [
                            {"const": data_set_val} for data_set_val in data_set_vals
                        ],
                    },
                    "rowSet": {"type": "array", "items": []},
                },
            }

            for column_val in data_set_vals:
                cleaned_column_val = "".join(
                    [val.capitalize() for val in column_val.split("_")]
                )

                temp_data_set["properties"]["rowSet"]["items"].append(
                    {"type": {"$ref": f"../schemas/{cleaned_column_val}.json"}}
                )

                if cleaned_column_val in parameters:
                    continue
                else:
                    parameters.add(cleaned_column_val)

                with (schema_dir / f"{cleaned_column_val}.json").open(
                    "w"
                ) as schema_file:
                    json.dump(
                        {"description": "[to do]", "type": "string"},
                        schema_file,
                        indent=2,
                    )

            with (data_set_dir / f"{data_set}.json").open("w") as data_set_file:
                json.dump(temp_data_set, data_set_file, indent=2)

    for openapi_dir in [schema_dir, parameter_dir, data_set_dir]:
        with (openapi_dir / "_index.json").open("w") as index_schema_file:
            json.dump(
                {
                    parameter: {"$ref": f"./{parameter}.json"}
                    for parameter in sorted(parameters)
                },
                index_schema_file,
                indent=2,
            )

    with openapi_file_path.open("w") as openapi_file:
        openapi.update(
            {
                "components": {
                    "parameters": {"$ref": "specification/parameters/_index.json"},
                    "schemas": {"$ref": "specification/schemas/_index.json"},
                }
            }
        )
        json.dump(openapi, openapi_file, indent=2)

    return


if __name__ == "__main__":
    working_dir = pathlib.Path(__file__).resolve().parents[1]
    generate_parameters(working_dir)
