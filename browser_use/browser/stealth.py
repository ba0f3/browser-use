"""
Stealth utilities for local Chromium.

This module intentionally keeps the init script small and auditable. It does not try to
be a perfect anti-fingerprinting solution; it only addresses a few high-signal
automation checks in a best-effort way.
"""

# Injected via CDP Page.addScriptToEvaluateOnNewDocument(source=..., runImmediately=True)
STEALTH_INIT_SCRIPT = r"""
(() => {
	"use strict";

	// --- webdriver flag ---
	try {
		Object.defineProperty(navigator, "webdriver", { get: () => undefined });
	} catch (_) {}

	// --- window.chrome shim (lightweight) ---
	try {
		if (!("chrome" in window)) {
			Object.defineProperty(window, "chrome", { value: { runtime: {} } });
		} else if (window.chrome && !("runtime" in window.chrome)) {
			Object.defineProperty(window.chrome, "runtime", { value: {} });
		}
	} catch (_) {}

	// --- Permissions API: normalize notifications ---
	// Some detectors call: navigator.permissions.query({ name: "notifications" })
	try {
		const originalQuery = window.navigator.permissions && window.navigator.permissions.query;
		if (originalQuery) {
			const query = function(parameters) {
				try {
					if (parameters && parameters.name === "notifications") {
						return Promise.resolve({ state: Notification.permission });
					}
				} catch (_) {}
				return originalQuery.apply(this, arguments);
			};
			Object.defineProperty(window.navigator.permissions, "query", { value: query });
		}
	} catch (_) {}
})();
"""

