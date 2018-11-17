module Flagellum.Init
(
  initialize,
  env,
  flagellumPoll,
  flagTest
) where

import Neovim
import Neovim.Log (infoM)

data E = E

flagellumPoll :: Neovim startupEnv Bool
flagellumPoll = return True

flagTest :: Neovim startupEnv Bool
flagTest = return True

env :: Neovim startupEnv ()
env = return ()

initialize :: Neovim startupEnv ()
initialize = return ()
