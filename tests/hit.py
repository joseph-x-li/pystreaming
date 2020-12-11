from turbojpeg import TurboJPEG, TJSAMP_420, TJFLAG_FASTDCT, TJFLAG_FASTUPSAMPLE
from turbojpeg import TurboJPEG, TJFLAG_FASTDCT, TJFLAG_FASTUPSAMPLE
import numpy as np
from functools import partial
import cv2, blosc
from pystreaming.video.testimages.imageloader import loadimage

frame = np.asarray(loadimage(5))
decoder = partial(TurboJPEG().decode, flags=(TJFLAG_FASTDCT + TJFLAG_FASTUPSAMPLE))
# range(0, 101, 10):
for q in [50]:
    input(f"Testing {q=}")
    encoder = partial(
        TurboJPEG().encode, quality=q, jpeg_subsample=TJSAMP_420, flags=TJFLAG_FASTDCT
    )
    buf = encoder(frame)
    print(len(buf))
    recover = decoder(buf)
    cv2.imshow("window", recover)
    cv2.waitKey(0)


# x = np.asarray(loadimage(5))
# y = np.random.randint(0, 50, x.shape, dtype=np.uint8)
# # y = y - (y % 10)
# # y = np.zeros(x.shape, dtype=np.uint8)

# cv2.imshow("xxx", x)
# cv2.waitKey(0)
# cv2.imshow("xxx", y)
# cv2.waitKey(0)

# a = encoder(x)
# b = encoder(y)
# x = decoder(a)
# y = decoder(b)
# print(f"{len(a)=}")
# print(f"{len(b)=}")

# cv2.imshow("xxx", x)
# cv2.waitKey(0)
# cv2.imshow("xxx", y)
# cv2.waitKey(0)

# cap = cv2.VideoCapture(0)

# frm = [None, None]

# import time

# for i in range(90):
#     frame = cap.read()[1]
#     if i == 20 or i == 75:
#         frm[i // 40] = frame
#     print(i)

# s = time.time()
# diff = (frm[1]//2 + 128) - (frm[0]//2) 
# eend = time.time()
# print(f"TIME{eend - s}")

# cv2.imshow("xxx", frm[0])
# cv2.waitKey(0)
# cv2.imshow("xxx", frm[1])
# cv2.waitKey(0)
# cv2.imshow("xxx", diff)
# cv2.waitKey(0)


# s = time.time()
# e1 = encoder(frm[0])
# e2 = encoder(frm[1])
# end = time.time()
# print(f"DOUBLEENC:{end - s}")
# edelta = encoder(diff)

# e1rec = decoder(e1)
# e2rec = decoder(e2)
# edeltarec = decoder(edelta)
# import pdb; pdb.set_trace()
# e2tmpc = (edeltarec.astype(np.int32))*2 - 256 + e1rec
# e2tmpc = e2tmpc.astype(np.uint8)

# cv2.imshow("xxx", e1rec)
# cv2.waitKey(0)
# cv2.imshow("xxx", e2rec)
# cv2.waitKey(0)
# cv2.imshow("xxx", e2tmpc)
# cv2.waitKey(0)



# print(len(e1))
# print(len(blosc.compress(e1, typesize=8)))
# print(len(e2))
# print(len(edelta))


# encoder1 = partial(
#     TurboJPEG().encode, quality=50, jpeg_subsample=TJSAMP_420, flags=TJFLAG_FASTDCT
# )
# decoder = partial(TurboJPEG().decode, flags=(TJFLAG_FASTDCT + TJFLAG_FASTUPSAMPLE))