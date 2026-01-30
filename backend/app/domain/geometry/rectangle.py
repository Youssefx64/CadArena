from app.schemas.geometry import Point, RectangleGeometry


def rectangle_to_points(rect: RectangleGeometry):
    x = rect.origin.x
    y = rect.origin.y
    w = rect.width
    h = rect.height

    return [
        Point(x=x, y=y),
        Point(x=x + w, y=y),
        Point(x=x + w, y=y + h),
        Point(x=x, y=y + h),
    ]
