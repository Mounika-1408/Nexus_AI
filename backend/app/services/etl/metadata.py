def calculate_metadata(
    original_rows,
    cleaned_rows,
    duplicates_removed,
    invalid_rows
):
    if original_rows == 0:
        quality_score = 0

    else:
        problematic_rows = duplicates_removed + invalid_rows

        quality_score = (
            (original_rows - problematic_rows)
            / original_rows
        ) * 100

    return {
        "total_rows": original_rows,
        "cleaned_rows": cleaned_rows,
        "duplicates_removed": duplicates_removed,
        "invalid_rows": invalid_rows,
        "data_quality_score": round(quality_score, 2),
        "status": "completed"
    }