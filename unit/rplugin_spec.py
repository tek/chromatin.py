from kallikrein import Expectation, kf
from kallikrein.expectable import kio

from amino.test import fixture_path, temp_dir
from amino import IO
from amino.case import Case
from amino.test.spec import SpecBase

from chromatin.model.rplugin import DirRplugin, SiteRplugin, DistRplugin, Rplugin

from test.base import simple_rplugin

name = 'flagellum'


class RpluginSpec(SpecBase):
    '''
    dir rplugin $dir_rplugin
    site rplugin $site_rplugin
    venv rplugin $venv_rplugin
    default rplugin $default
    '''

    def dir_rplugin(self) -> Expectation:
        dir = fixture_path('rplugin', name, name)
        spec = f'dir:{dir}'
        plugin = DirRplugin.cons(name, str(dir))
        return kf(simple_rplugin, name, spec) == plugin

    def site_rplugin(self) -> Expectation:
        pkg = 'subprocess'
        spec = f'site:{pkg}'
        plugin = SiteRplugin.cons(pkg, pkg)
        pkg_bad = 'invalid$(%&'
        spec_bad = f'site:{pkg_bad}'
        plugin_bad = SiteRplugin.cons(pkg_bad, pkg_bad)
        return (
            (kf(simple_rplugin, pkg, spec) == plugin) &
            (kf(simple_rplugin, pkg_bad, spec_bad) == plugin_bad)
        )

    def venv_rplugin(self) -> Expectation:
        spec = f'venv:{name}'
        plugin = DistRplugin.cons(name, name)
        return kf(simple_rplugin, name, spec) == plugin

    def default(self) -> Expectation:
        plugin = DistRplugin.cons(name, name)
        return kf(simple_rplugin, name, name) == plugin


__all__ = ('RpluginSpec',)
