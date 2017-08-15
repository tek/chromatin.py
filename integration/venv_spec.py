from kallikrein import k, Expectation

from integration._support.base import ChromatinPluginIntegrationSpec

from amino.test import temp_dir


class VenvSpec(ChromatinPluginIntegrationSpec):
    '''
    test $test
    '''

    def test(self) -> Expectation:
        self.vim.vars.set_p('venv_dir', str(temp_dir('add', 'venv')))
        self.vim.cmd_sync('Cram fn')
        self._wait(.1)
        self.vim.cmd_sync('Cram lenses')
        self._wait(.1)
        self.vim.cmd_sync('CrmSetupPlugins')
        self._wait(6)
        return k(1) == 1

__all__ = ('VenvSpec',)
