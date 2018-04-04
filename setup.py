from setuptools import setup, find_packages


if __name__ == '__main__':
    setup(
        name='mc-vasp-example',
        version='0.1',
        packages=find_packages(),
        install_requires=[
            'aiida',
            'aiida-vasp'
        ],
        reentry_register=True,
        entry_points={
            'aiida.workflows': [
                'mc-vasp.example = mc_vasp_example.bands_wf:ExampleWorkflow',
                'mc-vasp.test = mc_vasp_example.test_wf:TestWorkflow'
            ]
        }

    )
