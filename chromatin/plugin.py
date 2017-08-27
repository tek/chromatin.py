from ribosome.record import Record, str_field

from amino import List, Either, Map


class VimPlugin(Record):
    name = str_field()
    spec = str_field()

    @staticmethod
    def from_config(data: dict) -> Either[str, 'VimPlugin']:
        m = Map(data)
        def create(spec: str) -> VimPlugin:
            name = m.lift('name') | spec
            return VimPlugin(name=str(name), spec=str(spec))
        return m.lift('spec').to_either(f'plugin data {data} missing attribute `spec`').map(create)

    def _arg_desc(self) -> List[str]:
        return List(self.name, self.spec)

__all__ = ('VimPlugin',)
