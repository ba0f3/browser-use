"""
Integration tests for local stealth mode.

These tests verify that enabling BrowserProfile(stealth_mode=True) injects a small
init script on new documents and applies basic headless UA normalization.
"""

import pytest
from pytest_httpserver import HTTPServer

from browser_use.browser import BrowserSession
from browser_use.browser.profile import (
	BrowserProfile,
	DEFAULT_STEALTH_CHROME_VERSION,
	_get_default_stealth_user_agent,
)


@pytest.fixture(scope="session")
def http_server():
	server = HTTPServer()
	server.start()

	server.expect_request("/").respond_with_data(
		"<!doctype html><html><head><title>Stealth Test</title></head><body><h1>ok</h1></body></html>",
		content_type="text/html",
	)

	yield server
	server.stop()


@pytest.fixture(scope="session")
def base_url(http_server):
	return f"http://{http_server.host}:{http_server.port}"


@pytest.fixture(scope="function")
async def browser_session():
	session = BrowserSession(
		browser_profile=BrowserProfile(
			headless=True,
			user_data_dir=None,
			keep_alive=True,
			stealth_mode=True,
		)
	)
	await session.start()
	yield session
	await session.kill()


async def test_stealth_init_script_masks_navigator_webdriver(browser_session, base_url):
	await browser_session.navigate_to(f"{base_url}/")
	cdp_session = await browser_session.get_or_create_cdp_session()
	result = await cdp_session.cdp_client.send.Runtime.evaluate(
		params={"expression": "navigator.webdriver", "returnByValue": True},
		session_id=cdp_session.session_id,
	)
	assert result.get("result", {}).get("value") is None


def test_stealth_headless_ua_normalization():
	profile = BrowserProfile(headless=True, user_data_dir=None, stealth_mode=True)
	args = profile.get_args()
	ua_args = [a for a in args if a.startswith("--user-agent=")]
	assert len(ua_args) == 1
	assert "HeadlessChrome" not in ua_args[0]


def test_stealth_headless_respects_explicit_user_agent_in_args():
	explicit = "--user-agent=ExplicitUA/1.0"
	profile = BrowserProfile(
		headless=True,
		user_data_dir=None,
		stealth_mode=True,
		args=[explicit],
	)
	args = profile.get_args()
	ua_args = [a for a in args if a.startswith("--user-agent=")]
	assert ua_args == [explicit]


def test_stealth_headless_respects_user_agent_field():
	explicit = "ExplicitUA/2.0"
	profile = BrowserProfile(
		headless=True,
		user_data_dir=None,
		stealth_mode=True,
		user_agent=explicit,
	)
	args = profile.get_args()
	ua_args = [a for a in args if a.startswith("--user-agent=")]
	assert ua_args == [f"--user-agent={explicit}"]


def test_stealth_chrome_version_env_valid(monkeypatch):
	monkeypatch.setenv('STEALTH_CHROME_VERSION', '200.1.2.3')
	ua = _get_default_stealth_user_agent()
	assert 'Chrome/200.1.2.3' in ua
	assert 'HeadlessChrome' not in ua


def test_stealth_chrome_version_env_invalid_falls_back(monkeypatch):
	monkeypatch.setenv('STEALTH_CHROME_VERSION', 'not-a-version;;')
	ua = _get_default_stealth_user_agent()
	assert f'Chrome/{DEFAULT_STEALTH_CHROME_VERSION}' in ua
	assert 'not-a-version' not in ua
