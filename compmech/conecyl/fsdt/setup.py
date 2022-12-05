import os
from Cython.Build import cythonize


def configuration(parent_package='', top_path=None):
    from numpy.distutils.misc_util import Configuration

    if os.name == 'nt':
        if os.environ.get('CYTHON_TRACE_NOGIL') is not None:
            #NOTE removing openmp and optimizations for CI
            args_linear = ['/O0', '/openmp']
            args_nonlinear = ['/O0', '/openmp', '/fp:fast']
        else:
            args_linear = ['/openmp']
            args_nonlinear = ['/openmp', '/fp:fast']
    else:
        if os.environ.get('CYTHON_TRACE_NOGIL') is not None:
            #NOTE removing openmp and optimizations for CI
            args_linear = ['-O0', '-fopenmp']
            args_nonlinear = ['-O0', '-fopenmp', '-ffast-math']
        else:
            args_linear = ['-fopenmp']
            args_nonlinear = ['-fopenmp', '-ffast-math']

    config = Configuration('fsdt', parent_package, top_path)
    config.add_extension('fsdt_commons_bc1', ['fsdt_commons_bc1.pyx'],
              extra_compile_args=args_linear)
    config.add_extension('fsdt_commons_bc2', ['fsdt_commons_bc2.pyx'],
              extra_compile_args=args_linear)
    config.add_extension('fsdt_commons_bc3', ['fsdt_commons_bc3.pyx'],
              extra_compile_args=args_linear)
    config.add_extension('fsdt_commons_bc4', ['fsdt_commons_bc4.pyx'],
              extra_compile_args=args_linear)
    config.add_extension('fsdt_commons_bcn', ['fsdt_commons_bcn.pyx'],
              extra_compile_args=args_linear)

    config.add_extension('fsdt_donnell_bc1_linear',
              ['fsdt_donnell_bc1_linear.pyx'],
              extra_compile_args=args_linear)
    config.add_extension('fsdt_donnell_bc2_linear',
              ['fsdt_donnell_bc2_linear.pyx'],
              extra_compile_args=args_linear)
    config.add_extension('fsdt_donnell_bc3_linear',
              ['fsdt_donnell_bc3_linear.pyx'],
              extra_compile_args=args_linear)
    config.add_extension('fsdt_donnell_bc4_linear',
              ['fsdt_donnell_bc4_linear.pyx'],
              extra_compile_args=args_linear)
    config.add_extension('fsdt_donnell_bcn_linear',
              ['fsdt_donnell_bcn_linear.pyx'],
              extra_compile_args=args_linear)

    config.add_extension('fsdt_geier1997_bc2',
              ['fsdt_geier1997_bc2.pyx'],
              extra_compile_args=args_linear)
    config.add_extension('fsdt_sanders_bcn_linear',
              ['fsdt_sanders_bcn_linear.pyx'],
              extra_compile_args=args_linear)
    config.add_extension('fsdt_shadmehri2012_bc2',
              ['fsdt_shadmehri2012_bc2.pyx'],
              extra_compile_args=args_linear)
    config.add_extension('fsdt_shadmehri2012_bc3',
              ['fsdt_shadmehri2012_bc3.pyx'],
              extra_compile_args=args_linear)

    config.add_extension('fsdt_donnell_bc1_nonlinear',
              ['fsdt_donnell_bc1_nonlinear.pyx'],
              extra_compile_args=args_nonlinear)
    config.add_extension('fsdt_donnell_bc2_nonlinear',
              ['fsdt_donnell_bc2_nonlinear.pyx'],
              extra_compile_args=args_nonlinear)
    config.add_extension('fsdt_donnell_bc3_nonlinear',
              ['fsdt_donnell_bc3_nonlinear.pyx'],
              extra_compile_args=args_nonlinear)
    config.add_extension('fsdt_donnell_bc4_nonlinear',
              ['fsdt_donnell_bc4_nonlinear.pyx'],
              extra_compile_args=args_nonlinear)
    config.add_extension('fsdt_donnell_bcn_nonlinear',
              ['fsdt_donnell_bcn_nonlinear.pyx'],
              extra_compile_args=args_nonlinear)

    cythonize(config.ext_modules)

    config.make_config_py()

    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())
