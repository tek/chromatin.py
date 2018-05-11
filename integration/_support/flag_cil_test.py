from amino import List
from amino.test import fixture_path

from chromatin.model.rplugin import VenvRplugin


name1 = 'flagellum'
name2 = 'cilia'
path1 = fixture_path('rplugin', name1)
path2 = fixture_path('rplugin', name2)
plugin1 = VenvRplugin.cons(name1, name1)
plugin2 = VenvRplugin.cons(name2, name2)
plugins = List(
    dict(name=name1, spec=str(path1)),
    dict(name=name2, spec=str(path2)),
)

__all__ = ('name1', 'name2', 'path1', 'path2', 'plugin1', 'plugin2', 'plugins',)
