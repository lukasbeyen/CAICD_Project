"""pytest setup for CAD/tests, loaded by pytest before the test files.

The course code builds all its paths from os.getcwd() (yaml file, netlist, spice models, no_backup/), so the tests
must run from CAD/. This moves there first, so the tests also work when pytest is started from the repo root or from
an IDE's test explorer.
"""
import os
import sys

CAD_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(CAD_DIR)
sys.path.insert(0, CAD_DIR)  # so that "import ngspice_interface" works from anywhere
