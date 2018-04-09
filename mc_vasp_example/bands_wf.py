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
        spec.input('num_procs', valid_type=Int)
        spec.input('max_walltime', valid_type=Int)
        spec.outline(
            cls.set_defaults,
            cls.run_relaxation,
            cls.run_seekpath,
            cls.run_scf,
            cls.run_bands,
            cls.get_bands
        )
        spec.output('bands', valid_type=DataFactory('array.bands'))

    def set_defaults(self):
        self.ctx.inputs = self.get_inputs_template()
        self.ctx.inputs.relax_ISIF = self.inputs.relax_ISIF.value or 2

    def run_relaxation(self):
        vasp_proc = CalculationFactory('vasp.vasp').process()
        params = vex.RELAXATION_INCAR_TEMPLATE
        params.update({'isif': self.ctx.inputs.relax_ISIF})
        inputs = vex.make_inputs(
            codename = self.inputs.vasp_codename.value,
            incar=params,
            structure=self.inputs.structure,
            kpoints=vex.get_relaxation_kpoints(structure=self.inputs.structure, distance=self.inputs.relax_kpts_dist.value),
            settings={
                'parser_settings': {
                    'add_structure': True
                }
            },
            queue_name=self.inputs.queue_name.value,
            num_procs=self.inputs.num_procs.value
        )
        inputs._options.max_wallclock_seconds = self.inputs.max_walltime.value
        result = submit(vasp_proc, **inputs)
        return ToContext(relax_run=result)
    
    def run_seekpath(self):
        path_out = seekpath(self.ctx.relax_run.out.output_structure)
        self.ctx.relaxed_structure = path_out['primitive_structure']
        self.ctx.kpoints_path = path_out['explicit_kpoints']

    def run_scf(self):
        vasp_proc = CalculationFactory('vasp.vasp').process()
        params = vex.SCF_INCAR_TEMPLATE
        inputs = vex.make_inputs(
            codename = self.inputs.vasp_codename.value,
            incar=params,
            structure= self.ctx.relaxed_structure,
            kpoints=vex.get_relaxation_kpoints(structure=self.inputs.structure, distance=self.inputs.relax_kpts_dist.value),
            settings={
                'parser_settings': {
                    'add_structure': True, 'add_chgcar': True
                },
                'ADDITIONAL_RETRIEVE_LIST': ['WAVECAR', 'CHGCAR'],
            },
            queue_name=self.inputs.queue_name.value,
            num_procs=self.inputs.num_procs.value
        )
        inputs._options.max_wallclock_seconds = self.inputs.max_walltime.value
        result = submit(vasp_proc, **inputs)
        return ToContext(scf_run=result)

    def run_bands(self):
        vasp_proc = CalculationFactory('vasp.vasp').process()
        params = vex.BANDS_INCAR_TEMPLATE
        params.update({'icharg': 11})
        inputs = vex.make_inputs(
            codename = self.inputs.vasp_codename.value,
            incar=params,
            structure=self.ctx.relaxed_structure,
            kpoints=self.ctx.kpoints_path,
            settings={'parser_settings': {'add_bands': True, 'add_dos': True}},
            queue_name=self.inputs.queue_name.value,
            num_procs=self.inputs.num_procs.value
        )
        inputs._options.max_wallclock_seconds = self.inputs.max_walltime.value
        inputs.charge_density = self.ctx.scf_run.out.chgcar
        result = submit(vasp_proc, **inputs)
        return ToContext(bands_run=result)

    def get_bands(self):
        self.out('bands', self.ctx.bands_run.out.output_band)


