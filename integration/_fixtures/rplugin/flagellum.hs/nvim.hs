import Neovim

import Flagellum.Plugin (plugin)

main :: IO ()
main = neovim defaultConfig {plugins = plugins defaultConfig ++ [plugin]}
