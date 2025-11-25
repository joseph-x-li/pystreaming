from typing import List

TEST_S: int = 0
TEST_M: int = 1
TEST_L: int = 2
IMAG_S: int = 3
IMAG_M: int = 4
IMAG_L: int = 5

_lookup: List[str] = [
    "640x480_c.png",
    "1280x720_c.png",
    "1920x1080_c.png",
    "640x480_i.png",
    "1280x720_i.png",
    "1920x1080_i.png",
]


def loadimage(enum: int):  # type: ignore[return]  # PIL.Image not easily typed
    """Load a test image or a test card.

    Args:
        enum (int): One of
            pystreaming.TEST_S
            pystreaming.TEST_M
            pystreaming.TEST_L
            pystreaming.IMAG_S
            pystreaming.IMAG_M
            pystreaming.IMAG_L

    Raises:
        IndexError: Raised when received enum is not defined.

    Returns:
        PIL.Image: Image requested.
    """
    from PIL import Image
    import os

    try:
        truepath = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), _lookup[enum]
        )
        return Image.open(truepath)
    except IndexError:
        raise IndexError(f"Unrecognized image option: {enum}")
