from fairlearn.metrics import demographic_parity_difference, selection_rate, MetricFrame

THRESHOLD = 0.10  # flag if approval rates differ by more than 10 points


def audit(y_true, y_pred, sensitive):
    """Demographic parity difference for each sensitive attribute."""
    results = {}
    for attr in sensitive.columns:
        dpd = demographic_parity_difference(
            y_true, y_pred, sensitive_features=sensitive[attr]
        )
        rates = MetricFrame(
            metrics=selection_rate, y_true=y_true, y_pred=y_pred,
            sensitive_features=sensitive[attr],
        ).by_group

        ratio = rates.min() / rates.max()
        
        results[attr] = {
            "demographic_parity_difference": round(float(dpd), 3),
            "approval_rate_by_group": {str(k): round(float(v), 3) for k, v in rates.items()},
            "flag": bool(dpd > THRESHOLD),
            "disparate_impact_ratio": round(float(ratio), 3),
            "four_fifths_flag": bool(ratio < 0.8),
        }
    return results