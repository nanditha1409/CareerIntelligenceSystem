"""
Optional export service:
- CSV export for recommendation/evaluation payloads.
- No impact on existing APIs unless export endpoint is called.
"""

import csv
import io


def recommendations_to_csv(recommendations: list[dict]) -> str:
    # StringIO keeps export in-memory and fast for small/medium result sets.
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["domain", "confidence", "salary", "demand", "top_skills"])
    for rec in recommendations:
        writer.writerow(
            [
                rec.get("domain", ""),
                rec.get("confidence", ""),
                rec.get("salary", ""),
                rec.get("demand", ""),
                ", ".join(rec.get("top_skills", [])),
            ]
        )
    return buffer.getvalue()


def readiness_to_csv(readiness_payload: dict) -> str:
    # Single-row export for assessment report snapshots.
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["domain", "skill_match", "assessment_performance", "readiness_score", "label"])
    writer.writerow(
        [
            readiness_payload.get("domain", ""),
            readiness_payload.get("skill_match", ""),
            readiness_payload.get("assessment_performance", ""),
            readiness_payload.get("readiness_score", ""),
            readiness_payload.get("label", ""),
        ]
    )
    return buffer.getvalue()
