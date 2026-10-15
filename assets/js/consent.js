// Loads Google Analytics and Microsoft Clarity only after the visitor accepts.
(function () {
  var KEY = 'gc_analytics_consent' // 'granted' | 'denied'
  var GA_ID = 'G-GTLNJGZN8P'
  var CLARITY_ID = 'yaar5e101p'

  window.dataLayer = window.dataLayer || []
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments) }

  function read() { try { return localStorage.getItem(KEY) } catch (e) { return null } }
  function write(v) { try { localStorage.setItem(KEY, v) } catch (e) { /* private mode */ } }

  // Embedded previews: no banner over the preview, and no tracking there.
  function isFramed() { try { return window.self !== window.top } catch (e) { return true } }

  var loaded = false
  function loadAnalytics() {
    if (loaded) return
    loaded = true
    var ga = document.createElement('script')
    ga.async = true
    ga.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID
    document.head.appendChild(ga)
    window.gtag('js', new Date())
    window.gtag('config', GA_ID)

    ;(function (c, l, a, r, i, t, y) {
      c[a] = c[a] || function () { (c[a].q = c[a].q || []).push(arguments) }
      t = l.createElement(r); t.async = 1; t.src = 'https://www.clarity.ms/tag/' + i
      y = l.getElementsByTagName(r)[0]; y.parentNode.insertBefore(t, y)
    })(window, document, 'clarity', 'script', CLARITY_ID)
  }

  function closeBanner() {
    var el = document.getElementById('gc-consent')
    if (el) el.remove()
  }

  function choose(value) {
    write(value)
    closeBanner()
    if (value === 'granted') loadAnalytics()
    // Declining after accepting can't unload scripts already running; a reload stops them.
    else if (loaded) location.reload()
  }

  function showBanner() {
    if (document.getElementById('gc-consent')) return
    var wrap = document.createElement('div')
    wrap.id = 'gc-consent'
    wrap.setAttribute('role', 'dialog')
    wrap.setAttribute('aria-live', 'polite')
    wrap.setAttribute('aria-label', 'Analytics preferences')
    wrap.innerHTML =
      '<style>' +
      '#gc-consent{position:fixed;left:16px;right:16px;bottom:16px;z-index:2147483000;max-width:560px;margin:0 auto;' +
      'background:#ffffff;color:#111827;border:1px solid #e5e7eb;border-radius:14px;box-shadow:0 10px 30px rgba(0,0,0,.15);' +
      'padding:16px;font:14px/1.45 Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;text-align:left}' +
      '#gc-consent p{margin:0 0 12px;color:inherit}' +
      '#gc-consent a{color:#1d4ed8}' +
      '#gc-consent .gc-row{display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap}' +
      '#gc-consent button{font:inherit;font-weight:600;border-radius:10px;padding:8px 14px;cursor:pointer;border:1px solid #d1d5db;' +
      'background:transparent;color:#111827 !important;height:auto;line-height:1.4;text-transform:none;letter-spacing:normal;box-shadow:none}' +
      '#gc-consent button.gc-accept{background:#1d4ed8 !important;border-color:#1d4ed8 !important;color:#fff !important}' +
      '</style>' +
      '<p>This site uses Google Analytics and Microsoft Clarity to understand how it\'s used. ' +
      'They only run if you accept. <a href="/privacy.html">Privacy policy</a></p>' +
      '<div class="gc-row"><button type="button" class="gc-decline">Decline</button>' +
      '<button type="button" class="gc-accept">Accept</button></div>'
    wrap.querySelector('.gc-accept').addEventListener('click', function () { choose('granted') })
    wrap.querySelector('.gc-decline').addEventListener('click', function () { choose('denied') })
    document.body.appendChild(wrap)
  }

  // Footer "Cookie settings" links call this to change the choice.
  window.gcConsent = { open: showBanner }

  function init() {
    if (isFramed()) return
    var choice = read()
    if (choice === 'granted') loadAnalytics()
    else if (choice !== 'denied') showBanner()
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init)
  else init()
})()
