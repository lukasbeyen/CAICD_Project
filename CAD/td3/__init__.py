from .agent import TD3
try:
    # the TAs' compiled SAC baseline (lab sessions 3-4, slide 2): only loads on x86-64 Linux with Python 3.9
    # (the student server); elsewhere (e.g. our ARM VM) td3 must still import, for TD3 and the tests
    from .sac_baseline import SAC
except ImportError:
    SAC = None
from .buffer import ReplayBuffer
