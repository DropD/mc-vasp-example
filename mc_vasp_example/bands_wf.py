import vasp_example as vex
vex.load_dbenv_if_not_loaded()
from aiida.orm import DataFactory, CalculationFactory
from aiida.work import WorkChain, submit, workfunction
from aiida.work.workchain import ToContext
from aiida.work.db_types import Int, Str, Float
from aiida.tools.data.array.kpoints import get_explicit_kpoints_path


@workfunction
def seekpath(structure):
    return get_explicit_kpoints_path(structure=structure)


class ExampleWorkflow(WorkChain):
    @classmethod
    def define(cls, spec):
        super(ExampleWorkflow, cls).define(spec)
        spec.input('structure', valid_type=DataFactory('structure'))
        spec.input('relax_ISIF', valid_type=Int)
        spec.input('relax_kpts_dist', valid_type=Float)
        spec.input('vasp_codename', valid_type=Str)
        spec.input('queue_name', valid_type=Str)
        spec.outline(
            cls.set_defaults,
            cls.run_relaxation,
            cls.run_bands,
            cls.get_bands
        )
        spec.output('bands', valid_type=DataFactory('array.bands'))

    def set_defaults(self):
        self.ctx.inputs = self.get_inputs_template()
        self.ctx.inputs.relax_ISIF = self.inputs.relax_ISIF.value or 2

    def run_relaxation(self):
        pass
        vasp_proc = CalculationFactory('vasp.vasp').process()
        params = vex.RELAXATION_INCAR_TEMPLATE
        params.update({'isif': self.ctx.inputs.relax_ISIF})
        inputs = vex.make_inputs(
            codename = self.inputs.vasp_codename.value,
            incar=params,
            structure=self.inputs.structure,
            kpoints=vex.get_relaxation_kpoints(structure=self.inputs.structure, distance=self.inputs.relax_kpts_dist.value),
            settings={'parser_settings': {'add_structure': True, 'add_chgcar': True, 'add_wavecar': True}},
            queue_name=self.inputs.queue_name.value
        )
        result = submit(vasp_proc, **inputs)
        return ToContext(relax_run=result)

    def run_bands(self):
        vasp_proc = CalculationFactory('vasp.vasp').process()
        params = vex.BANDS_INCAR_TEMPLATE
        params.update({'istart': 2 if self.ctx.inputs.relax_ISIF > 2 else 1})
        path_out = seekpath(self.ctx.relax_run.out.output_structure)
        inputs = vex.make_inputs(
            codename = self.inputs.vasp_codename,
            incar=vex.BANDS_INCAR_TEMPLATE,
            structure=path_out['primitive_structure'],
            kpoints=path_out['explicit_kpoints'],
            settings={'parser_settings': {'add_bands': True, 'add_dos': True}},
            queue_name=self.innputs.queue_name
        )
        inputs.wavefunctions = self.ctx.relax_run.out.wavecar
        inputs.charge_density = self.ctx.relax_run.out.chgcar
        result = submit(vasp_proc, **inputs)
        return ToContext(bands_run=result)

    def get_bands(self):
        self.out('bands', self.ctx.bands_run.out.output_band)


