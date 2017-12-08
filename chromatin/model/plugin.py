from uuid import UUID, uuid4

from amino import List, Either, Map
from amino.dat import Dat


class RpluginSpec(Dat['RpluginSpec']):

    @staticmethod
    def cons(name: str, spec: str, id: UUID=None) -> 'RpluginSpec':
        return RpluginSpec(name, spec, id or uuid4())

    def __init__(self, name: str, spec: str, id: UUID) -> None:
        self.name = name
        self.spec = spec
        self.uuid = id

    @staticmethod
    def from_config(data: dict) -> Either[str, 'RpluginSpec']:
        m = Map(data)
        def create(spec: str) -> RpluginSpec:
            name = m.lift('name') | spec
            return RpluginSpec.cons(name=str(name), spec=str(spec))
        return m.lift('spec').to_either(f'plugin data {data} missing attribute `spec`').map(create)

    @staticmethod
    def simple(name: str) -> 'RpluginSpec':
        return RpluginSpec.cons(name=name, spec=name)

    def _arg_desc(self) -> List[str]:
        return List(self.name, self.spec)

__all__ = ('RpluginSpec',)
