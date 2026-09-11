from email.message import EmailMessage

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def make_mhtml(html: str) -> bytes:
    message = EmailMessage()
    message["Subject"] = "Sample HLD"
    message.make_related()
    message.add_related(html, subtype="html", charset="utf-8")
    return message.as_bytes()


def test_extract_endpoint():
    payload = make_mhtml("<html><body><h1>Overview</h1><h2>Scope</h2></body></html>")
    response = client.post(
        "/api/v1/documents/extract-sections",
        files={"file": ("sample.mhtml", payload, "multipart/related")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["section_count"] == 2
    assert body["sections"][0]["children"][0]["title"] == "Scope"


def test_reject_wrong_extension():
    response = client.post(
        "/api/v1/documents/extract-sections",
        files={"file": ("sample.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 415
