/**
 * Braillewright dark mode toggle (2.0.22).
 *
 * - Follows the operating system's color scheme by default.
 * - The toggle button (fixed, lower right corner) lets the visitor choose
 *   manually; the choice is remembered in localStorage.
 * - The button's accessible name is "Toggle theme, currently X". Changing it
 *   on a polite live region announces the new theme to screen readers.
 */
(function () {
	'use strict';

	var STORAGE_KEY = 'bw-theme';
	var BUTTON_ID = 'bw-theme-toggle';
	var ICON_DARK = '\u263E'; // crescent moon: shown in light mode, activates dark
	var ICON_LIGHT = '\u2600'; // sun: shown in dark mode, activates light

	function getSystemTheme() {
		if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
			return 'dark';
		}
		return 'light';
	}

	function getStoredTheme() {
		try {
			var stored = window.localStorage.getItem(STORAGE_KEY);
			if (stored === 'dark' || stored === 'light') {
				return stored;
			}
		} catch (e) {
			/* private mode etc: fall through to system */
		}
		return null;
	}

	function getCurrentTheme() {
		var stored = getStoredTheme();
		if (stored) {
			return stored;
		}
		return getSystemTheme();
	}

	function labelFor(theme) {
		return 'Toggle theme, currently ' + theme;
	}

	function applyTheme(theme) {
		document.documentElement.setAttribute('data-theme', theme);
		var button = document.getElementById(BUTTON_ID);
		if (button) {
			button.setAttribute('aria-label', labelFor(theme));
			var icon = button.querySelector('.bw-theme-toggle-icon');
			if (icon) {
				icon.textContent = theme === 'dark' ? ICON_LIGHT : ICON_DARK;
			}
		}
	}

	function init() {
		applyTheme(getCurrentTheme());

		var button = document.getElementById(BUTTON_ID);
		if (button) {
			button.addEventListener('click', function () {
				var current = document.documentElement.getAttribute('data-theme') || getSystemTheme();
				var next = current === 'dark' ? 'light' : 'dark';
				try {
					window.localStorage.setItem(STORAGE_KEY, next);
				} catch (e) {
					/* private mode etc: theme still switches for this visit */
				}
				applyTheme(next);
			});
		}

		// If the visitor never chose manually, keep following the OS.
		if (window.matchMedia) {
			var media = window.matchMedia('(prefers-color-scheme: dark)');
			var onChange = function () {
				if (!getStoredTheme()) {
					applyTheme(getSystemTheme());
				}
			};
			if (media.addEventListener) {
				media.addEventListener('change', onChange);
			} else if (media.addListener) {
				media.addListener(onChange);
			}
		}
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}
})();
