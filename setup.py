from setuptools import setup, find_packages

setup(
      name = "langerhansGUI",
      version = "1.0.0",
      description = "GUI for Langerhans package.",
      author = "Jan Zmazek",
      url = "https://github.com/janzmazek/langerhansGUI",
      license = "MIT License",
      packages = find_packages(exclude=['*test']),
      entry_points = {
            'console_scripts': [
                  'langui = langerhansGUI.run:run',
            ]
      },
      install_requires = ['langerhans', 'pyyaml', 'numpy', 'scipy']
)
