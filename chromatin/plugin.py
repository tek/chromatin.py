from ribosome.record import Record, str_field, uuid_field

from amino import List, Either, Map


class RpluginSpec(Record):
    uuid = uuid_field()
    name = str_field()
    spec = str_field()

    @staticmethod
    def from_config(data: dict) -> Either[str, 'RpluginSpec']:
        m = Map(data)
        def create(spec: str) -> RpluginSpec:
            name = m.lift('name') | spec
            return RpluginSpec(name=str(name), spec=str(spec))
        return m.lift('spec').to_either(f'plugin data {data} missing attribute `spec`').map(create)

    def _arg_desc(self) -> List[str]:
        return List(self.name, self.spec)

__all__ = ('RpluginSpec',)
