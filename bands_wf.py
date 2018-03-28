import vasp_example as vex
vex.load_dbenv_if_not_loaded()
from aiida.orm import DataFactory, CalculationFactory
from aiida.work import WorkChain, submit
from aiida.work.workchain import ToContext
from aiida.work.db_types import Int, Str, Float


class ExampleWorkflow(WorkChain):
    @classmethod
    def define(cls, spec):
        super(ExampleWorkflow, cls).define(spec)
        spec.input('structure', valid_type=DataFactory('structure'))
        spec.input('relax_ISIF', valid_type=Int)
        spec.input('relax_kpts_dist', valid_type=Float)
        spec.input('vasp_codename', valid_type=Str)
        spec.outline(
            # ~ cls.set_defaults,
            cls.run_relaxation,
            cls.run_bands,
            cls.get_bands
        )
        spec.output('bands', valid_type=DataFactory('array.bands'))

    def set_defaults(self):
        self.ctx.inputs.relax_ISIF = self.inputs.relax_ISIF.value or 4

    def run_relaxation(self):
        pass
        vasp_proc = CalculationFactory('vasp.vasp').process()
        params = vex.RELAXATION_INCAR_TEMPLATE
        params.update({'isif': self.inputs.relax_ISIF.value})
        inputs = vex.make_inputs(
            codename = self.inputs.vasp_codename,
            incar=params,
            structure=self.inputs.structure,
            kpoints=vex.get_relaxation_kpoints(structure=self.inputs.structure, distance=self.inputs.relax_kpts_dist.value),
            settings={'parser_settings': {'add_structure': True}}
        )
        result = submit(vasp_proc, **inputs)
        return ToContext(relax_run=result)

    def run_bands(self):
        vasp_proc = CalculationFactory('vasp.vasp').process()
        inputs = vex.make_inputs(
            codename = self.inputs.vasp_codename,
            incar=vex.BANDS_INCAR_TEMPLATE,
            structure=self.ctx.relax_run.out.output_structure,
            kpoints='path',
            settings={'parser_settings': {'add_bands': True, 'add_dos': True}}
        )
        result = submit(vasp_proc, **inputs)
        return ToContext(bands_run=result)

    def get_bands(self):
        self.out('bands', self.ctx.bands_run.out.output_band)


