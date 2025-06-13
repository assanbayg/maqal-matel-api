def paginated_response(
    results: list,
    total: int,
    page: int,
    limit: int,
    message: str,
):
    """Helper function for consistent pagination"""
    return {
        "results": results,
        "pagination": {
            "total_items": total,
            "current_page": page,
            "per_page": limit,
            "total_pages": (total + limit - 1) // limit,
            "has_next": page * limit < total,
            "has_previous": page > 1,
        },
        "message": message,
    }
