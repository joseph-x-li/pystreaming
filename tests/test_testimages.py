import pystreaming as ps


def test_test_images():
    enums = [
        ps.TEST_S,
        ps.TEST_M,
        ps.TEST_L,
        ps.IMAG_S,
        ps.IMAG_M,
        ps.IMAG_L,
    ]

    for e in enums:
        _ = ps.loadimage(e)

    try:
        ps.loadimage(-1212)
        raise AssertionError("Expected IndexError for invalid enum")
    except IndexError:
        pass
