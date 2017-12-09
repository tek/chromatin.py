from kallikrein import k, Expectation
from kallikrein.matchers.maybe import be_just

from ribosome.test.integration.run import DispatchHelper
from ribosome.trans.messages import Info

from amino import Map, List, Right, Path
from amino.test.spec import SpecBase
from amino.test import temp_dir, fixture_path

from chromatin import config
from chromatin.model.rplugin import Rplugin
from chromatin.components.core.trans.setup import show_plugins_message
from chromatin.model.venv import Venv, ActiveVenv

name = 'flagellum'


class ShowSpec(SpecBase):
    '''
    show one plugin $one
    '''

    @property
    def spec(self) -> str:
        return str(fixture_path('rplugin', name))

    def one(self) -> Expectation:
        dir = temp_dir('rplugin', 'venv')
        vars = dict(
            chromatin_rplugins=[dict(name=name, spec=self.spec)],
            chromatin_venv_dir=str(dir),
        )
        venv = Venv(name, dir / name, Right(Path('/dev/null')), Right(Path('/dev/null')))
        channel = 3
        pid = 1111
        active = ActiveVenv(venv, channel, pid)
        plugin = Rplugin.cons('flagellum', self.spec)
        helper0 = DispatchHelper.cons(config, 'core', vars=vars)
        data0 = helper0.state.data
        data = data0.copy(
            plugins=List(plugin),
            venvs=Map({name: venv}),
            active=List(active),
            installed=List(venv),
        )
        helper = helper0.copy(state=helper0.state.copy(data=data))
        r = helper.loop('chromatin:command:show_plugins').unsafe(helper.vim)
        return k(r.message_log.head).must(be_just(Info(show_plugins_message(dir, List(plugin)))))

__all__ = ('ShowSpec',)
