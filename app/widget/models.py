from enum import IntEnum, unique

import qtawesome as qta
from PyQt5.Qt import QIcon
from hbutils.model import int_enum_loads


@int_enum_loads(enable_int=False, name_preprocess=str.upper, )
@unique
class ProcessingStatus(IntEnum):
    PENDING = 0
    WAITING = 1
    PROCESSING = 2
    COMPLETED = 3
    ERROR = 4

    @property
    def text(self):
        return self.name.lower().capitalize()

    @property
    def icon(self) -> QIcon:
        if self == self.PENDING:
            return qta.icon('fa5.sticky-note', color='grey')
        elif self == self.WAITING:
            return qta.icon('fa.clock-o', color='yellow')
        elif self == self.PROCESSING:
            return qta.icon('fa.hourglass-1', color='blue')
        elif self == self.COMPLETED:
            return qta.icon('fa.check', color='green')
        elif self == self.ERROR:
            return qta.icon('fa.remove', color='red')
        else:
            raise ValueError(f'Unknown status - {repr(self)}.')


@int_enum_loads(enable_int=False, name_preprocess=str.upper, )
@unique
class NameStatus(IntEnum):
    NOTHING = 0
    INDEPENDENT = 1
    DEPENDENT = 2

    @property
    def text(self):
        return self.name.lower().capitalize()

    @property
    def icon(self) -> QIcon:
        if self == self.NOTHING:
            return qta.icon('mdi.do-not-disturb', color='grey')
        elif self == self.INDEPENDENT:
            return qta.icon('ri.input-cursor-move', color='#e97311')
        elif self == self.DEPENDENT:
            return qta.icon('msc.output', color='blue')
        else:
            raise ValueError(f'Unknown status - {repr(self)}.')

    @property
    def next(self) -> 'NameStatus':
        if self == self.NOTHING:
            return self.INDEPENDENT
        elif self == self.INDEPENDENT:
            return self.DEPENDENT
        elif self == self.DEPENDENT:
            return self.NOTHING
        else:
            raise ValueError(f'Unknown status - {repr(self)}.')
