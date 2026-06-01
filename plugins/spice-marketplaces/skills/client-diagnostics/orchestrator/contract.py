"""Sub-skill output contract — JSON schema + validator + computed-layer hash."""
import hashlib
import json
import jsonschema

SCHEMA = {
    "type": "object",
    "required": ["sub_skill", "version", "client", "window", "computed", "drafted", "data_quality"],
    "properties": {
        "sub_skill": {"type": "string"},
        "version": {"type": "string"},
        "client": {"type": "string"},
        "window": {
            "type": "object",
            "required": ["start", "end"],
            "properties": {"start": {"type": "string"}, "end": {"type": "string"}},
        },
        "computed": {
            "type": "object",
            "required": ["metrics", "radar_contributions", "tier_contributions", "findings", "charts"],
            "properties": {
                "metrics": {"type": "object"},
                "radar_contributions": {"type": "object", "additionalProperties": {"type": "number"}},
                "tier_contributions": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "required": ["score", "flag", "reasons"],
                        "properties": {
                            "score": {"type": "number"},
                            "flag": {"enum": ["green", "yellow", "red", "new"]},
                            "reasons": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
                "findings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["pattern_id", "severity", "scope", "evidence", "estimated_impact_usd", "deliverable_trigger"],
                        "properties": {
                            "pattern_id": {"type": "string"},
                            "severity": {"enum": ["low", "medium", "high", "foundation"]},
                            "scope": {"type": "string"},
                            "evidence": {"type": "object"},
                            "estimated_impact_usd": {"type": ["number", "null"]},
                            "deliverable_trigger": {
                                "type": "object",
                                "required": ["skill", "params"],
                                "properties": {"skill": {"type": "string"}, "params": {"type": "object"}},
                            },
                        },
                    },
                },
                "charts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["id", "path"],
                        "properties": {"id": {"type": "string"}, "path": {"type": "string"}},
                    },
                },
            },
        },
        "drafted": {
            "type": "object",
            "required": ["toggle_title", "toggle_prose", "win_risk_opp_candidates"],
            "properties": {
                "toggle_title": {"type": "string"},
                "toggle_prose": {"type": "string"},
                "win_risk_opp_candidates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["type", "headline"],
                        "properties": {
                            "type": {"enum": ["win", "risk", "opportunity"]},
                            "headline": {"type": "string"},
                            "value_usd": {"type": ["number", "null"]},
                            "pattern_id": {"type": "string"},  # optional, used for cross-sub-skill dedup
                            "severity": {"enum": ["low", "medium", "high", "foundation"]},
                        },
                    },
                },
            },
        },
        "data_quality": {
            "type": "object",
            "required": ["completeness", "gaps"],
            "properties": {
                "completeness": {"type": "number"},
                "gaps": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
}


class ContractError(Exception):
    pass


def validate(payload: dict) -> None:
    try:
        jsonschema.validate(payload, SCHEMA)
    except jsonschema.ValidationError as e:
        raise ContractError(str(e)) from e


def computed_hash(payload: dict) -> str:
    """Hash only the deterministic subset per spec §Verification.

    Excludes: charts[].path, findings[].evidence, drafted, data_quality.
    Includes: metrics, radar_contributions, tier_contributions,
              findings[].{pattern_id, severity, scope, estimated_impact_usd}.
    """
    c = payload["computed"]
    deterministic = {
        "metrics": c["metrics"],
        "radar_contributions": c["radar_contributions"],
        "tier_contributions": c["tier_contributions"],
        "findings": [
            {
                "pattern_id": f["pattern_id"],
                "severity": f["severity"],
                "scope": f["scope"],
                "estimated_impact_usd": f["estimated_impact_usd"],
            }
            for f in c["findings"]
        ],
    }
    serialized = json.dumps(deterministic, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode()).hexdigest()
