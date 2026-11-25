from app.services.finance.document_store import _valid_backup_root


def test_empty_backup_dir_not_cwd(monkeypatch):
    monkeypatch.setenv("FINANCE_RECEIPTS_BACKUP_DIR", "")
    from app.config import get_settings

    get_settings.cache_clear()
    assert _valid_backup_root() is None
    get_settings.cache_clear()