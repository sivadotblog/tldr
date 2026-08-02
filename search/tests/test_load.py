from pathlib import Path
from unittest.mock import MagicMock, patch

from tldr_embeddings.load import run

FIXTURES = Path(__file__).parent / "fixtures"


@patch("tldr_embeddings.db.get_collection")
def test_reset_deletes_all_before_upsert(mock_get_collection):
    mock_collection = MagicMock()
    mock_collection.delete_many.return_value = MagicMock(deleted_count=3)
    mock_collection.bulk_write.return_value = MagicMock(upserted_count=1, modified_count=0)
    mock_get_collection.return_value = mock_collection

    result = run(FIXTURES, recent=None, dry_run=False, reset=True)

    assert result == 0
    mock_collection.delete_many.assert_called_once_with({})
    call_order = [c[0] for c in mock_collection.method_calls]
    assert call_order.index("delete_many") < call_order.index("bulk_write")


@patch("tldr_embeddings.db.get_collection")
def test_no_reset_skips_delete(mock_get_collection):
    mock_collection = MagicMock()
    mock_collection.bulk_write.return_value = MagicMock(upserted_count=1, modified_count=0)
    mock_get_collection.return_value = mock_collection

    result = run(FIXTURES, recent=None, dry_run=False, reset=False)

    assert result == 0
    mock_collection.delete_many.assert_not_called()
