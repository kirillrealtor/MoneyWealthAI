/**
 * Render-blocking theme bootstrap. Injected as a nonced inline <script> at the
 * very top of <body> so the correct theme class is on <html> *before first
 * paint* — no flash of the wrong theme on load or reload.
 *
 * Source of truth: localStorage("mw-theme") = "light" | "dark". Absent ⇒ follow
 * the OS preference. The theme store (useTheme/setTheme) keeps this in sync at runtime.
 */
export const THEME_STORAGE_KEY = "mw-theme";

export const THEME_SCRIPT = `(function(){try{var k="${THEME_STORAGE_KEY}";var s=localStorage.getItem(k);var m=window.matchMedia("(prefers-color-scheme: dark)").matches;var dark=s?s==="dark":m;var d=document.documentElement;d.classList.toggle("dark",dark);d.style.colorScheme=dark?"dark":"light";}catch(e){}})();`;
