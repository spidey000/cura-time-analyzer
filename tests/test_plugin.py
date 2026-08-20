import importlib.util


def test_plugin_metadata_contract():
    spec = importlib.util.spec_from_file_location("cura_time_analyzer_plugin", "__init__.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    metadata = module.getMetaData()

    assert metadata["plugin"]["name"] == "Cura Time Analyzer"
    assert metadata["plugin"]["supported_sdk_versions"] == ["6.5.0"]
    assert "extension" in module.register(None)
