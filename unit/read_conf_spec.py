from kallikrein import k, Expectation
from kallikrein.matchers.either import be_left
from kallikrein.matchers.maybe import be_just

from amino.test.spec import SpecBase
from amino import List, Right

from chromatin.model.rplugin import Rplugin, DirRplugin, SiteRplugin

conf_data = List(
    dict(spec='dir:/dev/null', name='null', pythonpath=['/some/path'], debug=True),
    dict(spec='site:plug'),
    [],
    dict(),
)


class ReadConfSpec(SpecBase):
    '''
    read rplugin config from vim data $read_conf
    '''

    def read_conf(self) -> Expectation:
        rplugins = conf_data.map(Rplugin.from_config)
        successes = List(
            Right(DirRplugin.cons('null', '/dev/null', True, List('/some/path'))),
            Right(SiteRplugin.cons('plug', 'plug')),
        )
        return (
            (k(rplugins[:2]) == successes) &
            k(rplugins.lift(2)).must(be_just(be_left)) &
            k(rplugins.lift(3)).must(be_just(be_left))
        )


__all__ = ('ReadConfSpec',)
