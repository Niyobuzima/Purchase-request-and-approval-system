"""
Validation report generator.
Creates structured validation reports with summaries.
"""

from datetime import datetime
from typing import Dict, List


def generate_validation_report(
    is_valid: bool,
    discrepancies: List[Dict],
    receipt_data: Dict,
    po_data: Dict
) -> Dict:
    """
    Generate comprehensive validation report.

    Args:
        is_valid: Whether validation passed
        discrepancies: List of discrepancy records
        receipt_data: Extracted receipt data
        po_data: Purchase order data

    Returns:
        Structured validation report
    """
    report = {
        'is_valid': is_valid,
        'validation_date': datetime.now().isoformat(),
        'po_number': po_data.get('po_number'),
        'receipt_number': receipt_data.get('receipt_number'),
        'discrepancies_count': len(discrepancies),
        'discrepancies': discrepancies,
        'receipt_data': receipt_data,
        'summary': _generate_summary(discrepancies, is_valid),
        'severity_breakdown': _count_by_severity(discrepancies),
        'type_breakdown': _count_by_type(discrepancies),
    }

    return report


def _generate_summary(discrepancies: List[Dict], is_valid: bool) -> str:
    """Generate human-readable validation summary."""
    if is_valid:
        return (
            "Receipt validation passed. All items and amounts match the "
            "purchase order within acceptable tolerance."
        )

    high = sum(1 for d in discrepancies if d.get('severity') == 'HIGH')
    medium = sum(1 for d in discrepancies if d.get('severity') == 'MEDIUM')
    low = sum(1 for d in discrepancies if d.get('severity') == 'LOW')

    parts = [f"Receipt validation failed with {len(discrepancies)} discrepancies:"]

    if high:
        parts.append(f"{high} high severity")
    if medium:
        parts.append(f"{medium} medium severity")
    if low:
        parts.append(f"{low} low severity")

    return " ".join(parts)


def _count_by_severity(discrepancies: List[Dict]) -> Dict[str, int]:
    """Count discrepancies by severity level."""
    counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}

    for discrepancy in discrepancies:
        severity = discrepancy.get('severity', 'LOW')
        counts[severity] = counts.get(severity, 0) + 1

    return counts


def _count_by_type(discrepancies: List[Dict]) -> Dict[str, int]:
    """Count discrepancies by type."""
    counts = {}

    for discrepancy in discrepancies:
        disc_type = discrepancy.get('type', 'UNKNOWN')
        counts[disc_type] = counts.get(disc_type, 0) + 1

    return counts
