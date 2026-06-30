from src.yolo_detect import classify_image


def test_promotional_classification():
    assert classify_image(["person", "bottle"]) == "promotional"


def test_product_display_classification():
    assert classify_image(["bottle"]) == "product_display"


def test_lifestyle_classification():
    assert classify_image(["person"]) == "lifestyle"


def test_other_classification():
    assert classify_image(["chair"]) == "other"
