from pystreaming.listlib.circularlist import CircularList, Empty
from pystreaming.listlib.circulardict import CircularOrderedDict


def testcircularlist():
    try:
        cl = CircularList(0)
        assert False
    except ValueError:
        pass

    cl = CircularList(1)
    assert len(cl) == 0
    assert not cl.full()
    assert cl.__repr__() == "[None] front: 0 back: 0"

    cl.push(1)
    assert len(cl) == 1

    cl.push(2)
    assert len(cl) == 1

    cl.push(3)
    assert cl.full()
    assert len(cl) == 1
    assert cl.__repr__() == "[3] front: 0 back: 0"

    assert cl.pop() == 3
    assert not cl.full()

    cl = CircularList(5)
    assert cl.__repr__() == "[None, None, None, None, None] front: 0 back: 0"
    cl.push(0)
    cl.push(1)
    cl.push(2)
    cl.push(3)
    assert cl.__repr__() == "[0, 1, 2, 3, None] front: 0 back: 4"
    assert len(cl) == 4

    cl.push(4)
    cl.push(5)
    cl.push(6)
    assert cl.__repr__() == "[5, 6, 2, 3, 4] front: 2 back: 2"
    assert len(cl) == 5

    assert cl.pop() == 2
    assert cl.__repr__() == "[5, 6, 2, 3, 4] front: 3 back: 2"
    assert len(cl) == 4

    assert cl.pop() == 3
    assert cl.pop() == 4

    assert cl[0] == 5
    try:
        print(cl[2])
        assert False
    except IndexError:
        pass

    cl[1] = 7
    try:
        cl[2] = 8
        assert False
    except IndexError:
        pass

    assert cl.pop() == 5
    assert cl.pop() == 7
    try:
        cl.pop()
        assert False
    except Empty:
        pass


def testcirculardict():
    try:
        cd = CircularOrderedDict(0)
        assert False
    except ValueError:
        pass

    cd = CircularOrderedDict(5)
    cd.insert_end(1, 1)
    cd.insert_end(2, 2)
    cd.insert_end(3, 3)
    cd.insert_end(4, 4)
    assert len(cd) == 4
    cd.insert_end(5, 5)
    assert len(cd) == 5
    cd.insert_end(6, 6)
    assert len(cd) == 5

    for k, i in zip(cd.keys(), range(2, 7)):
        assert k == i

    cd.insert_end(3, 100)
    cd[2] = -100
    assert cd[2] == -100

    try:
        cd[7] = 7
        assert False
    except KeyError:
        pass

    assert cd.__repr__() == "OrderedDict([(2, -100), (4, 4), (5, 5), (6, 6), (3, 100)])"

    cd.delete(2)
    assert len(cd) == 4
    assert cd.pop_front() == (4, 4)
    assert len(cd) == 3
    assert cd.pop_front() == (5, 5)
    assert len(cd) == 2
    assert cd.pop_front() == (6, 6)
    assert len(cd) == 1
    assert cd.pop_front() == (3, 100)
    assert len(cd) == 0
