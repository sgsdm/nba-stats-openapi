import pathlib
import json
import re

import yaml


def generate_parameters(dir: pathlib.Path) -> None:
    with (dir / "generator" / "analysis.json").open("r") as analysis_file:
        analysis: dict[str, dict] = json.loads(analysis_file.read())

    openapi_file_path = dir / "openapi.yaml"
    specification_dir = dir / "specification"
    parameter_dir = specification_dir / "parameters"
    path_dir = specification_dir / "paths"
    schema_dir = specification_dir / "schemas"
    data_set_dir = specification_dir / "data_sets"

    with (dir / "specification" / "frontmatter.yaml").open("r") as frontmatter_file:
        openapi: dict = yaml.safe_load(frontmatter_file.read())

    parameters: set[str] = set()
    data_sets: set[str] = set()
    openapi["paths"] = {}
    for endpoint, endpoint_vals in analysis.items():
        if endpoint_vals["status"] in ["deprecated", "invalid"]:
            continue
            
        print(endpoint)

        openapi["paths"][f"/{endpoint.lower()}"] = {
            "$ref": f"specification/paths/{endpoint}.yaml"
        }
        temp_path = {
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
                {"$ref": f"../parameters/{parameter}.yaml"}
            )

            temp_path["get"]["responses"]["200"]["content"]["application/json"][
                "schema"
            ]["properties"]["parameters"]["properties"][parameter] = {
                "$ref": f"../schemas/{parameter}.yaml"
            }

            if parameter in parameters:
                continue
            else:
                parameters.add(parameter)

            temp_param: dict = {
                "name": parameter,
                "description": "[to do]",
                "in": "query",
                "schema": {"$ref": f"../schemas/{parameter}.yaml"},
            }
            if parameter in endpoint_vals["required_parameters"]:
                temp_param["required"] = True
            with (parameter_dir / f"{parameter}.yaml").open("w") as param_file:
                param_file.write(yaml.safe_dump(temp_param, sort_keys=False))

            temp_schema: dict = {"description": "[to do]"}
            if parameter in endpoint_vals["nullable_parameters"]:
                temp_schema["type"] = [None, "string"]
                nullable = True
            else:
                temp_schema["type"] = "string"
                nullable = False

            if (pattern := endpoint_vals["parameter_patterns"][parameter]) is not None:
                if "{" in pattern:  # probably regex. probably.
                    temp_schema["pattern"] = pattern
                else:
                    temp_schema["enum"] = [
                        re.sub(r"[^a-zA-Z0-9\s\-]+", "", option)
                        for option in pattern.split("|")
                    ]
                    if nullable:
                        temp_schema["enum"].insert(0, None)

            with (schema_dir / f"{parameter}.yaml").open("w") as schema_file:
                schema_file.write(yaml.safe_dump(temp_schema, sort_keys=False))

        temp_path["get"]["responses"]["200"]["content"]["application/json"]["schema"][
            "properties"
        ]["resultSets"]["items"] = [
            {"type": {"$ref": f"../data_sets/{data_set}.yaml"}}
            for data_set in endpoint_vals["data_sets"]
        ]

        with (path_dir / f"{endpoint}.yaml").open("w") as path_file:
            path_file.write(yaml.safe_dump(temp_path, sort_keys=False))
    
    print("\n")

    for endpoint, endpoint_vals in analysis.items():
        if endpoint_vals["status"] in ["deprecated", "invalid"]:
            continue
        print(endpoint)

        if endpoint in ["LeagueDashPlayerShotLocations", "LeagueDashTeamShotLocations"]:
            continue

        for data_set, data_set_vals in endpoint_vals["data_sets"].items():
            if data_set in data_sets:
                continue
            else:
                data_sets.add(data_set)

            temp_data_set = {
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
                    {"type": {"$ref": f"../schemas/{cleaned_column_val}.yaml"}}
                )

                if cleaned_column_val in parameters:
                    continue
                else:
                    parameters.add(cleaned_column_val)

                with (schema_dir / f"{cleaned_column_val}.yaml").open(
                    "w"
                ) as schema_file:
                    schema_file.write(
                        yaml.safe_dump(
                            {"description": "[to do]", "type": "string"},
                            sort_keys=False,
                        )
                    )

            with (data_set_dir / f"{data_set}.yaml").open("w") as data_set_file:
                data_set_file.write(
                    yaml.safe_dump(
                        temp_data_set,
                        sort_keys=False,
                    )
                )

    for openapi_dir in [schema_dir, parameter_dir, data_set_dir]:
        with (openapi_dir / "_index.yaml").open("w") as index_schema_file:
            index_schema_file.write(
                yaml.safe_dump(
                    {
                        parameter: {"$ref": f"./{parameter}.yaml"}
                        for parameter in sorted(parameters)
                    },
                    sort_keys=False,
                )
            )

    with openapi_file_path.open("w") as openapi_file:
        openapi.update(
            {
                "components": {
                    "parameters": {"$ref": "specification/parameters/_index.yaml"},
                    "schemas": {"$ref": "specification/schemas/_index.yaml"},
                }
            }
        )
        openapi_file.write(yaml.safe_dump(openapi, sort_keys=False))

    return


if __name__ == "__main__":
    working_dir = pathlib.Path(__file__).resolve().parents[2]
    generate_parameters(working_dir)
