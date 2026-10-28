from homehub.core.errors import HomeHubError


def test_homehub_error_to_response():
    err = HomeHubError("NOT_FOUND", "Missing", status_code=404, details={"id": "1"})
    body = err.to_response()
    assert body.error.code == "NOT_FOUND"
    assert body.error.message == "Missing"
    assert body.error.details == {"id": "1"}
