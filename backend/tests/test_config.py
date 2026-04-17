from app.config import Settings


def test_cors_origins_list_parses_and_strips_slashes():
    s = Settings(CORS_ORIGINS="http://localhost:3000/, https://app.example.com/")
    assert s.cors_origins_list == ["http://localhost:3000", "https://app.example.com"]


def test_cors_origins_list_filters_empty():
    s = Settings(CORS_ORIGINS=",http://a.com,, ,http://b.com,")
    assert s.cors_origins_list == ["http://a.com", "http://b.com"]


def test_defaults_are_safe_for_dev_but_flagged():
    s = Settings()
    assert s.APP_NAME
    assert s.JWT_ALGORITHM == "HS256"
    assert s.ACCESS_TOKEN_EXPIRE_MINUTES > 0
