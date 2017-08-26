from ribosome.record import Record, str_field

from amino import List


class VimPlugin(Record):
    name = str_field()
    spec = str_field()

    def _arg_desc(self) -> List[str]:
        return List(self.name, self.spec)

__all__ = ('VimPlugin',)
