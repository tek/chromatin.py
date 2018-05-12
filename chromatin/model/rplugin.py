from typing import Type, Any, Tuple
import json

from amino import Either, Map, Regex, do, Do, Try, List, Maybe, Nil
from amino.dat import ADT, Dat
from amino.json.decoder import decode_json_type


class ConfigRplugin(Dat['ConfigRplugin']):

    def __init__(self, spec: str, name: Maybe[str], debug: Maybe[bool], pythonpath: Maybe[List[str]]) -> None:
        self.spec = spec
        self.name = name
        self.debug = debug
        self.pythonpath = pythonpath


class Rplugin(ADT['Rplugin']):

    @classmethod
    def cons(cls, name: str, spec: str, debug: Maybe[bool]=False, pythonpath: List[str]=Nil) -> 'Rplugin':
        return cls(name, spec, debug, pythonpath)

    def __init__(self, name: str, spec: str, debug: bool, pythonpath: List[str]) -> None:
        self.name = name
        self.spec = spec
        self.debug = debug
        self.pythonpath = pythonpath

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self)) and self.name == other.name and self.spec == other.spec

    @staticmethod
    @do(Either[str, 'Rplugin'])
    def from_config(data: dict) -> Do:
        json_conf = yield Try(json.dumps, data)
        conf = yield decode_json_type(json_conf, ConfigRplugin)
        return cons_rplugin(conf)

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


@do(Either[str, Tuple[Type[Rplugin], str]])
def parse_spec(raw_spec: str) -> Do:
    match = yield spec_rex.match(raw_spec)
    prefix, spec = yield match.all_groups('prefix', 'spec')
    tpe = yield ctors.lift(prefix).to_either('invalid rplugin spec prefix `{prefix}`')
    return tpe, spec


def cons_rplugin(conf: ConfigRplugin) -> Rplugin:
    tpe, spec = parse_spec(conf.spec).get_or_strict((VenvRplugin, conf.spec))
    return tpe.cons(
        conf.name.get_or_strict(spec),
        spec,
        conf.debug.get_or_strict(False),
        conf.pythonpath.get_or_strict(Nil),
    )


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
