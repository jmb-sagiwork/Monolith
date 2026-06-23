from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import threading
import time

from monolith.core.models import CapturedTarget


CATCH_SCRIPT = r"""
(() => {
  if (window.__monolithCatchActive) return;
  window.__monolithCatchActive = true;
  const style = document.createElement('style');
  style.id = '__monolithCatchStyle';
  style.textContent = '*[data-monolith-hover="true"] { outline: 3px solid #176b87 !important; cursor: crosshair !important; }';
  document.head.appendChild(style);
  let last = null;
  function selector(el) {
    if (el.id) return '#' + CSS.escape(el.id);
    const parts = [];
    while (el && el.nodeType === Node.ELEMENT_NODE && parts.length < 5) {
      let part = el.tagName.toLowerCase();
      if (el.className && typeof el.className === 'string') {
        const cls = el.className.trim().split(/\s+/)[0];
        if (cls) part += '.' + CSS.escape(cls);
      }
      const parent = el.parentElement;
      if (parent) {
        const siblings = Array.from(parent.children).filter(x => x.tagName === el.tagName);
        if (siblings.length > 1) part += `:nth-of-type(${siblings.indexOf(el) + 1})`;
      }
      parts.unshift(part);
      el = parent;
    }
    return parts.join(' > ');
  }
  function xpath(el) {
    if (el.id) return `//*[@id="${el.id}"]`;
    const parts = [];
    while (el && el.nodeType === Node.ELEMENT_NODE) {
      let idx = 1;
      let sib = el.previousElementSibling;
      while (sib) {
        if (sib.tagName === el.tagName) idx++;
        sib = sib.previousElementSibling;
      }
      parts.unshift(`${el.tagName.toLowerCase()}[${idx}]`);
      el = el.parentElement;
    }
    return '/' + parts.join('/');
  }
  function metadata(el) {
    const rect = el.getBoundingClientRect();
    return {
      css_selector: selector(el),
      xpath: xpath(el),
      tag: el.tagName.toLowerCase(),
      text: (el.innerText || el.value || '').trim().slice(0, 500),
      id: el.id || '',
      name: el.getAttribute('name') || '',
      class: el.className || '',
      placeholder: el.getAttribute('placeholder') || '',
      aria_label: el.getAttribute('aria-label') || '',
      role: el.getAttribute('role') || '',
      element_type: el.getAttribute('type') || '',
      bounding_box: {x: rect.x, y: rect.y, width: rect.width, height: rect.height},
      url: location.href,
      page_title: document.title
    };
  }
  window.__monolithMove = e => {
    if (last) last.removeAttribute('data-monolith-hover');
    last = e.target;
    last.setAttribute('data-monolith-hover', 'true');
  };
  window.__monolithClick = e => {
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();
    const data = metadata(e.target);
    window.__monolithStopCatch();
    window.monolith_capture(data);
    return false;
  };
  window.__monolithStopCatch = () => {
    document.removeEventListener('mousemove', window.__monolithMove, true);
    document.removeEventListener('click', window.__monolithClick, true);
    if (last) last.removeAttribute('data-monolith-hover');
    const style = document.getElementById('__monolithCatchStyle');
    if (style) style.remove();
    window.__monolithCatchActive = false;
  };
  document.addEventListener('mousemove', window.__monolithMove, true);
  document.addEventListener('click', window.__monolithClick, true);
})();
"""


class WebsitePlaywrightAdapter:
    def __init__(self) -> None:
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="monolith-playwright")
        self.playwright = None
        self.browser = None
        self.page = None
        self.current_url = ""
        self.stop_event = threading.Event()

    def open_browser(self, url: str) -> tuple[bool, str]:
        return self.executor.submit(self._open_browser, url).result()

    def _open_browser(self, url: str) -> tuple[bool, str]:
        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:
            return False, f"Playwright is not installed or unavailable: {exc}"
        try:
            if self.playwright is None:
                self.playwright = sync_playwright().start()
            if self.browser is None:
                self.browser = self.playwright.chromium.launch(headless=False)
            if self.page is None:
                self.page = self.browser.new_page()
            self.page.goto(url)
            self.current_url = self.page.url
            return True, f"Browser opened: {self.current_url}"
        except Exception as exc:
            return False, f"Browser could not launch/open URL: {exc}"

    def start_catch_mode(self, timeout: int = 60) -> CapturedTarget:
        return self.executor.submit(self._start_catch_mode, timeout).result()

    def _start_catch_mode(self, timeout: int = 60) -> CapturedTarget:
        if self.page is None:
            raise RuntimeError("Open a browser before starting catch mode.")
        self.stop_event.clear()
        captured: dict = {}
        event = threading.Event()

        def receive(_source, data):
            captured.update(data)
            event.set()

        try:
            self.page.expose_binding("monolith_capture", receive)
        except Exception:
            pass
        self.page.evaluate(CATCH_SCRIPT)
        deadline = time.time() + timeout
        while time.time() < deadline and not event.is_set() and not self.stop_event.is_set():
            self.page.wait_for_timeout(100)
        if not event.is_set():
            self._stop_catch_mode()
            if self.stop_event.is_set():
                raise RuntimeError("Website catch mode was stopped.")
            raise TimeoutError("Website catch mode timed out.")
        return CapturedTarget("Website", "Playwright", captured)

    def stop_catch_mode(self) -> None:
        self.stop_event.set()
        self.executor.submit(self._stop_catch_mode)

    def _stop_catch_mode(self) -> None:
        if self.page is not None:
            try:
                self.page.evaluate("window.__monolithStopCatch && window.__monolithStopCatch()")
            except Exception:
                pass

    def test_step(self, action: str, target: CapturedTarget | None, sample_input: str = "") -> tuple[str, str, str]:
        return self.executor.submit(self._test_step, action, target, sample_input).result()

    def _test_step(self, action: str, target: CapturedTarget | None, sample_input: str = "") -> tuple[str, str, str]:
        if self.page is None:
            return "Failed", "Browser is not open.", ""
        if not target:
            return "Failed", "No website element captured.", ""
        selector = target.metadata.get("css_selector") or target.metadata.get("xpath")
        if not selector:
            return "Failed", "Captured target has no selector.", ""
        try:
            locator = self.page.locator(selector).first
            if action == "Click":
                locator.click()
                return "Passed", "Website click test passed.", ""
            if action == "Type":
                if not sample_input:
                    return "Failed", "Sample input is required for Type.", ""
                locator.fill(sample_input)
                return "Passed", "Website type test passed.", ""
            text = locator.inner_text(timeout=3000)
            return "Passed", "Website extract test passed.", text
        except Exception as exc:
            return "Failed", f"Website {action.lower()} test failed: {exc}", ""
