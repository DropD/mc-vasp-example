"""Library for the VASP example notebook."""
import datetime

import numpy as np

from aiida import load_dbenv, is_dbenv_loaded


def load_dbenv_if_not_loaded():
    if not is_dbenv_loaded():
        load_dbenv()


def get_data_cls(descriptor):
    load_dbenv_if_not_loaded()
    from aiida.orm import DataFactory
    return DataFactory(descriptor)


def now_str():
    now = datetime.datetime.now()
    return now.strftime(format='%Y-%m-%d %H:%M')


def is_same_structure(left, right):
    result = True
    result &= bool(np.all(np.array(left.cell) - np.array(right.cell) < 1e-10))
    result &= bool(left.get_formula() == right.get_formula())
    result &= bool(left.get_kind_names() == right.get_kind_names())
    return result


def new_or_existing_structure(new_structure):
    structure_cls = get_data_cls('structure')
    result = new_structure
    query = structure_cls.querybuild()
    structures = [item[0] for item in query.all()]
    same_structures = [structure for structure in structures if is_same_structure(new_structure, structure)]
    if same_structures:
        result = same_structures[0]
    return result


RELAXATION_INCAR_TEMPLATE = {
    "istart": 0,
    "ismear": -1,
    "sigma": 0.2,
    "encut": 500,
    "algo": 'NORMAL',
    "ediff": 1E-6,
    "prec": 'H',
    "ibrion": 2,
    "nsw": 200,
    "melmin": 4,
    "ediffg": -0.01,
    "isif": 4
}

BANDS_INCAR_TEMPLATE = {
    'prec': 'NORMAL',
    'encut': 200,
    'ediff': 1e-8,
    'ialgo': 38,
    'ismear': 0,
    'nsw': 0,
    'sigma': 0.1
}

POTCAR_MAP = {
    'Si': 'Si',
    'Ga': 'Ga',
    'C': 'C_d',
    'Co': 'Co',
    'As': 'As'
}


def cached_parameter_data(new_params):
    load_dbenv_if_not_loaded()
    from aiida.orm import DataFactory

    result = DataFactory('parameter')(dict=new_params)
    param_cls = get_data_cls('parameter')
    query = param_cls.querybuild()
    filter_spec = {}
    for key, val in new_params.items():
        filter_spec['attributes.{}'.format(key)] = {'==': val}
    query.add_filter(param_cls, filter_spec)
    same_params = [item[0] for item in query.all()]
    if same_params:
        result = same_params[0]
    return result


def create_kpoints_path(structure):
    from aiida.tools.data.array.kpoints import get_explicit_kpoints_path
    return get_explicit_kpoints_path(structure=structure)


def create_structure_Si():
    structure_cls = get_data_cls('structure')
    alat = 5.4
    structure = structure_cls(cell=np.array([[.5, 0, .5], [.5, .5, 0], [0, .5, .5]]) * alat)
    structure.append_atom(position=np.array([.25, .25, .25]) * alat, symbols='Si')
    return structure


def make_inputs(incar, structure, kpoints, settings, codename):
    load_dbenv_if_not_loaded()
    from aiida.orm import CalculationFactory
    potcar_cls = get_data_cls('vasp.potcar')
    vasp_calc_proc = CalculationFactory('vasp.vasp').process()
    inputs = vasp_calc_proc.get_inputs_template()

    if kpoints == 'path':
        auto_kpoints = create_kpoints_path(structure)
        kpoints = auto_kpoints['explicit_kpoints']
        structure = new_or_existing_structure(auto_kpoints['conv_structure'])
    else:
        structure = new_or_existing_structure(structure)

    set_std_inputs(inputs, codename)
    inputs.kpoints = kpoints
    inputs.structure = structure
    inputs.potential = potcar_cls.get_potcars_from_structure(family_name='PBE', structure=inputs.structure, mapping=POTCAR_MAP)
    inputs.settings = cached_parameter_data(settings)
    inputs.parameters = cached_parameter_data(incar)

    return inputs


def set_std_options(inputs):
    inputs._options.max_wallclock_seconds = 180
    inputs._options.resources = {'num_machines': 1, 'num_mpiprocs_per_machine': 20}
    inputs._options.queue_name = 'dphys_compute'
    inputs._options.computer = inputs.code.get_computer()


def set_std_inputs(inputs, codename):
    load_dbenv_if_not_loaded()
    from aiida.orm import Code
    inputs._label = 'Demo {}'.format(now_str())
    inputs.code = codename
    inputs._description = 'This is a Demo calculation.'
    inputs['code'] = Code.get_from_string('vasp')
    set_std_options(inputs)


def get_relaxation_kpoints(structure, distance):
    relax_label = 'Demo - Relaxation Kpoints V2'
    kpoints_cls = get_data_cls('array.kpoints')
    query = kpoints_cls.querybuild()
    query.add_filter(kpoints_cls, {'label': {'==': relax_label}})
    if query.count() >= 1:
        return query.first()[0]
    relax_kpoints = kpoints_cls()
    relax_kpoints.set_cell_from_structure(structure)
    relax_kpoints.set_kpoints_mesh_from_density(distance=distance)
    relax_kpoints.label = relax_label
    return relax_kpoints
