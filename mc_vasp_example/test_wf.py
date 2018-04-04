import vasp_example as vex
vex.load_dbenv_if_not_loaded()

from aiida.orm import DataFactory
from aiida.work import WorkChain, workfunction
from aiida.work.db_types import Int, Str, Float

from bands_wf import seekpath


class TestWorkflow(WorkChain):
    @classmethod
    def define(cls, spec):
        super(TestWorkflow, cls).define(spec)
        spec.input('structure', valid_type=DataFactory('structure'))
        spec.input('sleeptime', valid_type=Int)
        spec.outline(
            cls.wait,
            cls.run_seekpath
        )
        spec.output('structure', valid_type=DataFactory('structure'))
        spec.output('kpoints', valid_type=DataFactory('array.kpoints'))

    def wait(self):
        from time import sleep
        sleep(self.inputs.sleeptime.value)

    def run_seekpath(self):
        seekpath_out = seekpath(self.inputs.structure)
        self.out('structure', seekpath_out['primitive_structure'])
        self.out('kpoints', seekpath_out['explicit_kpoints'])

