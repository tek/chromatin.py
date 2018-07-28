from typing import Type, Any, Tuple
import json

from amino import Either, Map, Regex, do, Do, Try, List, Maybe, Nil, Nothing, Path
from amino.dat import ADT, Dat
from amino.json.decoder import decode_json_type


class ConfigRplugin(Dat['ConfigRplugin']):

    def __init__(
            self,
            spec: str,
            name: Maybe[str],
            debug: Maybe[bool],
            pythonpath: Maybe[List[str]],
            interpreter: Maybe[str],
            extensions: Maybe[List[str]],
    ) -> None:
        self.spec = spec
        self.name = name
        self.debug = debug
        self.pythonpath = pythonpath
        self.interpreter = interpreter
        self.extensions = extensions


class Rplugin(ADT['Rplugin']):

    @classmethod
    def cons(
            cls,
            name: str,
            spec: str,
            debug: bool=False,
            pythonpath: List[str]=Nil,
            interpreter: Maybe[str]=Nothing,
            extensions: List[str]=Nil,
    ) -> 'Rplugin':
        return cls(name, spec, debug, pythonpath, interpreter, extensions)

    def __init__(
            self,
            name: str,
            spec: str,
            debug: bool,
            pythonpath: List[str],
            interpreter: Maybe[str],
            extensions: List[str],
    ) -> None:
        self.name = name
        self.spec = spec
        self.debug = debug
        self.pythonpath = pythonpath
        self.interpreter = interpreter
        self.extensions = extensions

    @property
    def pythonpath_str(self) -> None:
        return self.pythonpath.mk_string(':')

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
        return DistRplugin.cons(name=name, spec=name)


class DistRplugin(Rplugin):
    pass


class DirRplugin(Rplugin):
    pass


class SiteRplugin(Rplugin):
    pass


ctors: Map[str, Type[Rplugin]] = Map(
    dir=DirRplugin,
    site=SiteRplugin,
    venv=DistRplugin,
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
    tpe, spec = parse_spec(conf.spec).get_or_strict((DistRplugin, conf.spec))
    return tpe.cons(
        conf.name.get_or_strict(spec),
        spec,
        conf.debug.get_or_strict(False),
        conf.pythonpath.get_or_strict(Nil),
        conf.interpreter,
        conf.extensions.get_or_strict(Nil)
    )


class VenvRpluginMeta(ADT['VenvRplugin']):
    pass


class DistVenvRplugin(VenvRpluginMeta):

    def __init__(self, req: str) -> None:
        self.req = req


class DirVenvRplugin(VenvRpluginMeta):

    def __init__(self, dir: Path) -> None:
        self.dir = dir


class VenvRplugin(Dat['VenvRplugin']):

    def __init__(self, meta: VenvRpluginMeta, rplugin: Rplugin) -> None:
        self.meta = meta
        self.rplugin = rplugin


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


__all__ = ('Rplugin', 'DistRplugin', 'DirRplugin', 'SiteRplugin', 'cons_rplugin', 'ActiveRpluginMeta', 'ActiveRplugin',
           'VenvRplugin', 'DistVenvRplugin', 'DirVenvRplugin',)
