from pystreaming.listlib.circularlist import CircularOrderedDict

def collate(handler, buffer=10):
    initsize = buffer * 1.2
    print("collate primed")
    collate = CircularOrderedDict(initsize)
    for frame, idx in handler:
        if idx == 0:
            collate = CircularOrderedDict(initsize)
        collate.insert_end(idx, frame)
        print(f"\rbufsize: {len(collate)}, idx={idx}", end="")
        if len(collate) >= buffer:
            most_recent = min(collate.keys())
            yield collate[most_recent], most_recent
            collate.delete(most_recent)
