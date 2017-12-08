from amino.dat import ADT
from amino import Regex, Map, do, Do, Either, Right, Boolean, Path
from amino.regex import Match
from amino.dispatch import dispatch_alg

from chromatin.model.venvs import VenvFacade, VenvPackageAbsent
from chromatin.model.plugin import RpluginSpec


class PackageAdapter(ADT['PackageAdapter']):

    def __init__(self, plugin: RpluginSpec, spec: str) -> None:
        self.plugin = plugin
        self.spec = spec


class VenvAdapter(PackageAdapter):
    pass


class DirAdapter(PackageAdapter):
    pass


class SiteAdapter(PackageAdapter):
    pass


class PackageStatus(ADT['PackageStatus']):

    def __init__(self, adapter: PackageAdapter) -> None:
        self.adapter = adapter


class PackageReady(PackageStatus):
    pass


class PackageAbsent(PackageStatus):
    pass


ctors = Map(
    dir=DirAdapter,
    site=SiteAdapter,
    venv=VenvAdapter,
)
prefixes = ctors.k.mk_string('|')
spec_rex = Regex(f'(?P<prefix>{prefixes}):(?P<spec>.*)')


def parse_rplugin_spec(plugin: RpluginSpec) -> PackageAdapter:
    @do(Either[str, PackageAdapter])
    def select(match: Match) -> Do:
        prefix, spec = yield match.all_groups('prefix', 'spec')
        ctor = yield ctors.lift(prefix).to_either('invalid rplugin spec prefix `{prefix}`')
        yield Right(ctor(plugin, spec))
    return spec_rex.match(plugin.spec).flat_map(select) | (lambda: VenvAdapter(plugin, plugin.spec))


class PackageFacade:

    def __init__(self, venv_facade: VenvFacade) -> None:
        self.venv_facade = venv_facade
        self.ready = dispatch_alg(self, PackageAdapter, 'ready_')

    def check(self, plugin: RpluginSpec) -> PackageStatus:
        return self.ready(parse_rplugin_spec(plugin))

    def ready_dir_adapter(self, adapter: DirAdapter) -> PackageStatus:
        return Boolean(Path(adapter.spec).is_dir()).c(PackageReady(adapter), PackageAbsent(adapter))

    def ready_site_adapter(self, adapter: SiteAdapter) -> PackageStatus:
        return (
            Either.import_module(adapter.spec)
            .cata(lambda a: PackageAbsent(adapter), lambda a: PackageReady(adapter))
        )

    def ready_venv_adapter(self, adapter: VenvAdapter) -> PackageStatus:
        venv_status = self.venv_facade.check(adapter.plugin)
        package_status = Boolean(venv_status.exists and self.venv_facade.package_installed(venv_status.venv))
        ctor = package_status.cata(PackageReady, PackageAbsent)
        return ctor(adapter)


__all__ = ('PackageAdapter', 'VenvAdapter', 'DirAdapter', 'SiteAdapter', 'PackageFacade')
