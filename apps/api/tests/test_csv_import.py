import pytest

from app.services.finance.csv_import import import_bank_csv


class EmptyExec:
    def scalar_one_or_none(self):
        return None


class FakeSession:
    def __init__(self):
        self.added = []

    async def execute(self, stmt):
        return EmptyExec()

    def add(self, obj):
        self.added.append(obj)


@pytest.mark.asyncio
async def test_csv_import_basic():
    csv_text = "date,description,amount,id\n2025-06-01,Test payment,150.00,tx-1\n"
    result = await import_bank_csv(FakeSession(), csv_text)
    assert result.imported == 1
    assert result.errors == []


@pytest.mark.asyncio
async def test_csv_import_duplicate_skip():
    class DupSession(FakeSession):
        def __init__(self):
            super().__init__()
            self.seen = False

        async def execute(self, stmt):
            if not self.seen:
                self.seen = True
                return EmptyExec()

            class Hit:
                def scalar_one_or_none(self):
                    return object()

            return Hit()

    csv_text = "date,description,amount,id\n2025-06-01,A,10,tx-dup\n2025-06-02,B,20,tx-dup\n"
    result = await import_bank_csv(DupSession(), csv_text)
    assert result.imported == 1
    assert result.skipped_duplicates == 1