"""Show installed dependency license metadata without network calls."""

import json
from importlib.metadata import distributions

result = []
for distribution in distributions():
    metadata = distribution.metadata
    expression = metadata.get("License-Expression")
    classifiers = [
        value
        for value in metadata.get_all("Classifier", [])
        if value.startswith("License ::")
    ]
    result.append(
        {
            "name": metadata["Name"],
            "version": distribution.version,
            "license_expression": expression,
            "license_classifiers": classifiers,
            "notice": "See distribution license files if no expression is supplied.",
        }
    )
print(json.dumps(sorted(result, key=lambda item: item["name"].lower()), indent=2))
