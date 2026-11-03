from src.pages.lobby_page import LobbyPage


class _FakeLocator:
    def __init__(self, visible):
        self.visible = visible

    @property
    def first(self):
        return self

    def is_visible(self, timeout=None):
        return self.visible


class _FakePage:
    def __init__(self, visible):
        self.visible = visible
        self.last_selector = None

    def locator(self, selector):
        self.last_selector = selector
        return _FakeLocator(self.visible)


def test_login_button_locator_uses_fallback_selectors():
    page = _FakePage(visible=True)
    lobby = LobbyPage(page, {"url": "https://example.com"})

    lobby._login_button_locator()

    assert page.last_selector == ", ".join(LobbyPage.LOGIN_BUTTON_SELECTORS)


def test_is_logged_in_is_false_when_login_button_is_visible():
    page = _FakePage(visible=True)
    lobby = LobbyPage(page, {"url": "https://example.com"})

    assert lobby.is_logged_in() is False


def test_is_logged_in_is_true_when_login_button_is_not_visible():
    page = _FakePage(visible=False)
    lobby = LobbyPage(page, {"url": "https://example.com"})

    assert lobby.is_logged_in() is True
