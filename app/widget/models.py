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
