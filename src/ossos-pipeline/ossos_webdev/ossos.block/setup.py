from setuptools import setup

requires = [
    'pyramid',
]
namespace_packages=['ossos', ]
setup(name='ossos.block',
      entry_points="""\
      [paste.app_factory]
      main = ossos.overview:main
      """,
)
