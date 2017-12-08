from kallikrein import k, Expectation, kf

from amino.test import fixture_path, temp_dir

from chromatin.model.package import (PackageFacade, DirAdapter, parse_rplugin_spec, PackageAbsent, PackageReady,
                                     SiteAdapter, VenvAdapter)
from chromatin.model.venvs import VenvFacade
from chromatin.model.plugin import RpluginSpec

name = 'flagellum'


class RpluginSpecSpec:
    '''
    dir spec $dir_spec
    site spec $site_spec
    venv spec $venv_spec
    default spec $default
    '''

    @property
    def facade(self) -> PackageFacade:
        dir = temp_dir('rplugin', 'venv')
        return PackageFacade(VenvFacade(dir))

    def dir_spec(self) -> Expectation:
        dir = fixture_path('rplugin', name, name)
        spec = f'dir:{dir}'
        plugin = RpluginSpec.cons(name, spec)
        return (
            (kf(parse_rplugin_spec, plugin) == DirAdapter(plugin, plugin.spec)) &
            (kf(self.facade.check, plugin) == PackageReady(plugin))
        )

    def site_spec(self) -> Expectation:
        pkg = 'subprocess'
        spec = f'site:{pkg}'
        plugin = RpluginSpec.cons(pkg, spec)
        pkg_bad = 'invalid$(%&'
        spec_bad = f'site:{pkg_bad}'
        plugin_bad = RpluginSpec.cons(pkg_bad, spec_bad)
        return (
            (kf(parse_rplugin_spec, plugin) == SiteAdapter(plugin, plugin.spec)) &
            (kf(self.facade.check, plugin) == PackageReady(plugin)) &
            (kf(parse_rplugin_spec, plugin_bad) == SiteAdapter(plugin_bad, plugin_bad.spec)) &
            (kf(self.facade.check, plugin_bad) == PackageAbsent(plugin_bad))
        )

    def venv_spec(self) -> Expectation:
        spec = f'venv:{name}'
        plugin = RpluginSpec.cons(name, spec)
        return (
            (kf(parse_rplugin_spec, plugin) == VenvAdapter(plugin, plugin.spec)) &
            (kf(self.facade.check, plugin) == PackageAbsent(plugin))
        )

    def default(self) -> Expectation:
        plugin = RpluginSpec.cons(name, name)
        return (
            (kf(parse_rplugin_spec, plugin) == VenvAdapter(plugin, plugin.spec)) &
            (kf(self.facade.check, plugin) == PackageAbsent(plugin))
        )

__all__ = ('RpluginSpecSpec',)
