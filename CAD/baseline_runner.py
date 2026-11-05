"""
A script for using a baseline TD3 agent as a reference
"""
# Lab sessions 3-4, slide 2: the TAs' baseline is a compiled Soft Actor-Critic (SAC) agent.
# sac_runner.cpython-39-x86_64-linux-gnu.so (here) and td3/sac_baseline.cpython-39-x86_64-linux-gnu.so only load on
# x86-64 Linux with Python 3.9 (the student server). Run from CAD/:  python baseline_runner.py
import sac_runner as sr

sr.main()
