{-# LANGUAGE TemplateHaskell #-}

module Flagellum.Plugin(
  plugin
)
where

import Neovim

import Flagellum.Init (initialize, env, flagellumPoll, flagTest)

plugin :: Neovim (StartupConfig NeovimConfig) NeovimPlugin
plugin = do
  initialize
  wrapPlugin
    Plugin {
      environment = env,
      exports = [
        $(function' 'flagellumPoll) Sync,
        $(function' 'flagTest) Sync
      ]
    }
