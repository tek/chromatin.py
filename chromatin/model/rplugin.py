from typing import Type, Any

from uuid import UUID, uuid4

from amino import Either, Map, Regex, do, Do, Right
from amino.dat import ADT, Dat
from amino.regex import Match


class Rplugin(ADT['Rplugin']):

    @classmethod
    def cons(cls, name: str, spec: str) -> 'Rplugin':
        return cls(name, spec)

    def __init__(self, name: str, spec: str) -> None:
        self.name = name
        self.spec = spec

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self)) and self.name == other.name and self.spec == other.spec

    @staticmethod
    def from_config(data: dict) -> Either[str, 'Rplugin']:
        m = Map(data)
        def create(spec: str) -> Rplugin:
            name = m.lift('name') | spec
            return cons_rplugin(str(name), str(spec))
        return m.lift('spec').to_either(f'rplugin data {data} missing attribute `spec`').map(create)

    @staticmethod
    def simple(name: str) -> 'Rplugin':
        return VenvRplugin.cons(name=name, spec=name)


class VenvRplugin(Rplugin):
    pass


class DirRplugin(Rplugin):
    pass


class SiteRplugin(Rplugin):
    pass


ctors: Map[str, Type[Rplugin]] = Map(
    dir=DirRplugin,
    site=SiteRplugin,
    venv=VenvRplugin,
)
prefixes = ctors.k.mk_string('|')
spec_rex = Regex(f'(?P<prefix>{prefixes}):(?P<spec>.*)')


def cons_rplugin(name: str, raw_spec: str) -> Rplugin:
    @do(Either[str, Rplugin])
    def select(match: Match) -> Do:
        prefix, spec = yield match.all_groups('prefix', 'spec')
        ctor = yield ctors.lift(prefix).to_either('invalid rplugin spec prefix `{prefix}`')
        yield Right(ctor.cons(name, spec))
    return spec_rex.match(raw_spec).flat_map(select) | (lambda: VenvRplugin.cons(name, raw_spec))


class RpluginStatus(ADT['RpluginStatus']):

    def __init__(self, rplugin: Rplugin) -> None:
        self.rplugin = rplugin


class RpluginReady(RpluginStatus):
    pass


class RpluginAbsent(RpluginStatus):
    pass


class ActiveRpluginMeta(Dat['ActiveRpluginMeta']):

    def __init__(self, rplugin: str, channel: int, pid: int) -> None:
        self.rplugin = rplugin
        self.channel = channel
        self.pid = pid


class ActiveRplugin(Dat['ActiveRplugin']):

    def __init__(self, rplugin: Rplugin, meta: ActiveRpluginMeta) -> None:
        self.rplugin = rplugin
        self.meta = meta

    @property
    def name(self) -> str:
        return self.rplugin.name


__all__ = ('Rplugin', 'VenvRplugin', 'DirRplugin', 'SiteRplugin', 'cons_rplugin', 'RpluginStatus', 'RpluginReady',
           'RpluginAbsent', 'ActiveRpluginMeta', 'ActiveRplugin')
