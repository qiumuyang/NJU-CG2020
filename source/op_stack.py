import time
from my_plist import PList


class OpStack:
    gap = 1

    def __init__(self, parent):
        self.undoList = []
        self.redoList = []
        self.checkpoint = [None, None]
        self.parent = parent
        self.last_do = time.time()

    def clear(self):
        self.undoList = []
        self.redoList = []
        self.checkpoint = [None, None]

    def undoValid(self):
        return not not self.undoList

    def redoValid(self):
        return not not self.redoList

    def undo(self):
        assert(self.undoValid())
        item = self.undoList.pop()
        self.redoList.append(item)
        self.parent.actionChanged.emit()
        return item

    def redo(self):
        assert(self.redoValid())
        item = self.redoList.pop()
        self.undoList.append(item)
        self.parent.actionChanged.emit()
        return item

    def mergeTop(self, action):
        if self.undoList:
            top = self.undoList[-1]
            if top.type == Action.TRANSFORM and action.type == Action.TRANSFORM:
                if top.t_type == action.t_type and time.time() - self.last_do < self.gap:
                    top.p_list[1] = action.p_list[1]
                    return True
        return False

    def do(self, action):
        self.redoList = []
        if not self.mergeTop(action):
            self.undoList.append(action)
        self.last_do = time.time()
        self.parent.actionChanged.emit()

    def setCheckpoint(self):
        self.checkpoint[0] = self.undoList[-1] if self.undoList else None
        self.checkpoint[1] = self.redoList[-1] if self.redoList else None

    def needSave(self):
        v1 = self.checkpoint[0] == (
            self.undoList[-1] if self.undoList else None)
        v2 = self.checkpoint[1] == (
            self.redoList[-1] if self.redoList else None)
        return not v1 or not v2


class Action:
    ITEM = 1
    ITEMS = 2
    TRANSFORM = 3
    COLOR = 4

    def __init__(self, type, **kwargs):
        self.type = type
        acceptArgs = ['item', 'items', 'item_id', 'color', 'p_list', 't_type']
        for arg in acceptArgs:
            if arg in kwargs:
                vars(self)[arg] = kwargs[arg]
        if 'p_list' in kwargs:
            self.p_list[0] = PList(self.p_list[0])
            self.p_list[1] = PList(self.p_list[1])

    def __repr__(self):
        _id = " " + self.item_id if self.type in [3, 4] else ""
        arg = vars(self)[{1: 'item', 2: 'items',
                          3: 'p_list', 4: 'color'}[self.type]]
        return f"[{self.type}]{_id}: {arg}"

# None -> Item | OldItem -> NewItem | color | p_list
