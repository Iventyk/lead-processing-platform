from src.worker.consumer import dedup_key


def test_dedup_key_stable() -> None:
    payload = {
        "name": "Alex",
        "phone": "+123",
        "offer_id": "offer",
        "affiliate_id": "aff",
        "country": "UA",
    }
    assert dedup_key(payload) == dedup_key(payload)
