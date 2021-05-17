import pystreaming as ps

def test_testiamges():
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
        assert False
    except IndexError:
        pass