from ribosome.record import Record, str_field


class VimPlugin(Record):
    spec = str_field()

__all__ = ('VimPlugin',)
