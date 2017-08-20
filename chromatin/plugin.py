from ribosome.record import Record, str_field


class VimPlugin(Record):
    name = str_field()
    spec = str_field()

__all__ = ('VimPlugin',)
