from amino.case import Case
from amino import List, Path

from chromatin.model.rplugin import VenvRpluginMeta, DistVenvRplugin, DirVenvRplugin


class install_venv_rplugin_args(Case[VenvRpluginMeta, List[str]], alg=VenvRpluginMeta):

    def dist(self, rplugin: DistVenvRplugin) -> List[str]:
        return List(rplugin.req)

    def dir(self, meta: DirVenvRplugin) -> List[str]:
        req = Path(meta.dir) / 'requirements.txt'
        return List('-r', str(req))


__all__ = ('install_venv_rplugin_args',)
