from kallikrein import Expectation, kf

from amino.test import fixture_path, temp_dir

from chromatin.model.rplugin import DirRplugin, RpluginAbsent, RpluginReady, SiteRplugin, VenvRplugin, cons_rplugin
from chromatin.rplugin import RpluginFacade

name = 'flagellum'


class RpluginSpec:
    '''
    dir rplugin $dir_rplugin
    site rplugin $site_rplugin
    venv rplugin $venv_rplugin
    default rplugin $default
    '''

    @property
    def facade(self) -> RpluginFacade:
        dir = temp_dir('rplugin', 'venv')
        return RpluginFacade(dir)

    def dir_rplugin(self) -> Expectation:
        dir = fixture_path('rplugin', name, name)
        spec = f'dir:{dir}'
        plugin = DirRplugin.cons(name, str(dir))
        return (
            (kf(cons_rplugin, name, spec) == plugin) &
            (kf(self.facade.check, plugin) == RpluginReady(plugin))
        )

    def site_rplugin(self) -> Expectation:
        pkg = 'subprocess'
        spec = f'site:{pkg}'
        plugin = SiteRplugin.cons(pkg, pkg)
        pkg_bad = 'invalid$(%&'
        spec_bad = f'site:{pkg_bad}'
        plugin_bad = SiteRplugin.cons(pkg_bad, pkg_bad)
        return (
            (kf(cons_rplugin, pkg, spec) == plugin) &
            (kf(self.facade.check, plugin) == RpluginReady(plugin)) &
            (kf(cons_rplugin, pkg_bad, spec_bad) == plugin_bad) &
            (kf(self.facade.check, plugin_bad) == RpluginAbsent(plugin_bad))
        )

    def venv_rplugin(self) -> Expectation:
        spec = f'venv:{name}'
        plugin = VenvRplugin.cons(name, name)
        return (
            (kf(cons_rplugin, name, spec) == plugin) &
            (kf(self.facade.check, plugin) == RpluginAbsent(plugin))
        )

    def default(self) -> Expectation:
        plugin = VenvRplugin.cons(name, name)
        return (
            (kf(cons_rplugin, name, name) == plugin) &
            (kf(self.facade.check, plugin) == RpluginAbsent(plugin))
        )

__all__ = ('RpluginSpec',)
