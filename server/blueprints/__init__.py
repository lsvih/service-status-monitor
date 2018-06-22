import importlib
import os


def register_blueprint(app):
    for module_name in map(lambda x: x[:-3], filter(lambda x: x[0] is not '_', os.listdir('blueprints'))):
        module_spec = importlib.util.find_spec('blueprints.' + module_name)
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        app.register_blueprint(eval('module.' + module_name + '_blueprint'), url_prefix='/api')
