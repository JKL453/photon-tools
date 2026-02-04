from photon_tools.registry import register_loader, load

# check if registry routes by file suffix
def test_registry_routes_by_suffix(tmp_path):
    def dummy_loader(path, **kw):
        return {"ok": True, "path": str(path), "kw": kw}

    register_loader(".dummy", loader=dummy_loader, overwrite=True)

    p = tmp_path / "file.dummy"
    p.write_text("x")

    out = load(p, foo=123)
    assert out["ok"] is True
    assert out["kw"]["foo"] == 123