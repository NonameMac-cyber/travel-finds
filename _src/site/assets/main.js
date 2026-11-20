/* Privacy-friendly Cloudflare Web Analytics: aggregate, cookieless. */
(function () {
  "use strict";
  var token = "9baa29ee4bdb4f2fa47d801ab8595b0d";
  if (token === "" || window.__tfAnalyticsLoaded) return;
  window.__tfAnalyticsLoaded = true;
  var beacon = document.createElement("script");
  beacon.type = "module";
  beacon.src = "https://static.cloudflareinsights.com/beacon.min.js";
  beacon.setAttribute("data-cf-beacon", JSON.stringify({ token: token }));
  document.head.appendChild(beacon);
})();

/* ==========================================================================
   travel-affiliate landing helpers (vanilla JS, no external dependencies).
   1) injects the TravelPayouts White Label widget;
   2) builds affiliate links for the deal cards from site-config.js;
   3) shows a graceful fallback when the widget/links are not configured yet.
   ========================================================================== */
(function () {
  "use strict";

  var config = window.TRAVEL_CONFIG || {};
  var CONSENT_KEY = "tf-consent-v1";
  var widgetInjected = false;

  function getConsent() {
    try { return window.localStorage.getItem(CONSENT_KEY); } catch (e) { return null; }
  }

  function setConsent(value) {
    try { window.localStorage.setItem(CONSENT_KEY, value); } catch (e) {}
  }

  function showWidgetFallback() {
    var fallback = document.getElementById("widget-fallback");
    if (fallback) fallback.classList.add("is-visible");
  }

  function hideWidgetFallback() {
    var fallback = document.getElementById("widget-fallback");
    if (fallback) fallback.classList.remove("is-visible");
  }

  function showConsentBanner() {
    if (document.getElementById("tf-cookie-banner")) return;
    var link = document.querySelector('[data-legal="cookies"]');
    var href = link ? link.getAttribute("href") : "cookies.html";
    var isSpanish = (document.documentElement.lang || "").toLowerCase().indexOf("es") === 0;
    var title = isSpanish ? "Cookies y socios" : "Cookies &amp; partners";
    var text = isSpanish
      ? "Usamos almacenamiento esencial y cookies de socios para que el sitio funcione y para medir referencias de afiliados. La analítica de Cloudflare no usa cookies. Puedes aceptar las cookies de socios o usar el sitio solo con almacenamiento esencial."
      : "We use essential storage and partner cookies to keep the site working and measure affiliate referrals. Cloudflare analytics is cookieless. You can accept partner cookies or use the site with essential storage only.";
    var learn = isSpanish ? "Más información" : "Learn more";
    var essential = isSpanish ? "Solo esencial" : "Essential only";
    var acceptAll = isSpanish ? "Aceptar todo" : "Accept all";
    var banner = document.createElement("div");
    banner.id = "tf-cookie-banner";
    banner.className = "cookie-banner";
    banner.setAttribute("role", "dialog");
    banner.setAttribute("aria-labelledby", "tf-cookie-title");
    banner.innerHTML = '<div class="cookie-banner__text"><strong id="tf-cookie-title">' + title + '</strong><p>' + text + ' <a href="' + href + '">' + learn + '</a>.</p></div>' +
      '<div class="cookie-banner__actions"><button type="button" class="cookie-btn cookie-btn--ghost" data-consent="essential">' + essential + '</button><button type="button" class="cookie-btn cookie-btn--primary" data-consent="all">' + acceptAll + '</button></div>';
    document.body.appendChild(banner);
    banner.querySelectorAll("[data-consent]").forEach(function (button) {
      button.addEventListener("click", function () {
        var choice = button.getAttribute("data-consent");
        setConsent(choice);
        banner.remove();
        if (choice === "all") { injectWidget(); }
        else { showWidgetFallback(); }
      });
    });
  }

  function resetConsent() {
    try { window.localStorage.removeItem(CONSENT_KEY); } catch (e) {}
    window.location.reload();
  }

  function isPlaceholderValue(value) {
    return !value || /^YOUR_/.test(String(value));
  }

  function widgetUrl(locale) {
    var params = {
      promo_id: config.widget && config.widget.promoId,
      shmarker: config.marker,
      campaign_id: config.widget && config.widget.campaignId,
      locale: locale,
      powered_by: (config.widget && config.widget.poweredBy) || "true",
    };
    var query = Object.keys(params)
      .filter(function (key) {
        return params[key] !== undefined && params[key] !== "";
      })
      .map(function (key) {
        return encodeURIComponent(key) + "=" + encodeURIComponent(params[key]);
      })
      .join("&");
    return "https://tp.media/content?" + query;
  }

  function appendUtm(target, campaign, content) {
    // UTM contract: source=seo_en|seo_es, medium=seo (used only for long targets).
    // NOTE: for pre-generated branded short links (?tpk.ro) query params are not
    // documented, so UTM is only used when a *long* target URL is wrapped later
    // (Links API converts longURL + UTM into a short partner link server-side).
    var lang = (document.documentElement.lang || "en").toLowerCase();
    var params = {
      utm_source: lang === "es" ? "seo_es" : "seo_en",
      utm_medium: "seo",
      utm_campaign: campaign || "landing",
      utm_content: content || "widget",
    };
    var separator = target.indexOf("?") === -1 ? "?" : "&";
    var query = Object.keys(params)
      .map(function (key) {
        return encodeURIComponent(key) + "=" + encodeURIComponent(params[key]);
      })
      .join("&");
    return target + separator + query;
  }

  function programConfig(program) {
    return (config.programs && config.programs[program]) || null;
  }

  function affiliateUrl(program, target) {
    var programInfo = programConfig(program);
    if (!programInfo) {
      return null;
    }
    // Links API bakes sub_id into a short link, so each language needs its own
    // seo_en / seo_es link (programInfo.urls.{en,es}); fallback — programInfo.url.
    var lang = (document.documentElement.lang || "en").toLowerCase();
    var url = (programInfo.urls && programInfo.urls[lang]) || programInfo.url;
    if (isPlaceholderValue(url)) {
      return null;
    }
    // 2026: no tp.media/r links in the browser; deep links are converted via
    // the TravelPayouts Links API (tools/links_api.py) in the content pipeline.
    if (target && programInfo.deeplinkTemplate) {
      return programInfo.deeplinkTemplate
        .replace("{url}", url)
        .replace("{target_encoded}", encodeURIComponent(appendUtm(target, "site-landing", program)));
    }
    return url;
  }

  function injectWidget() {
    var host = document.getElementById("tp-widget");
    var fallback = document.getElementById("widget-fallback");
    if (host === null || widgetInjected) {
      return;
    }
    var locale = host.getAttribute("data-locale") || "ru";
    if (isPlaceholderValue(config.widget && config.widget.promoId)) {
      if (fallback) {
        fallback.classList.add("is-visible");
      }
      return;
    }
    widgetInjected = true;
    hideWidgetFallback();
    var script = document.createElement("script");
    script.charset = "utf-8";
    script.src = widgetUrl(locale);
    script.async = true;
    script.onerror = function () {
      if (fallback) {
        fallback.classList.add("is-visible");
      }
    };
    host.appendChild(script);
  }

  function wireDealCards() {
    var cards = document.querySelectorAll("[data-affiliate-program]");
    Array.prototype.forEach.call(cards, function (card) {
      var program = card.getAttribute("data-affiliate-program");
      var target = card.getAttribute("data-affiliate-target") || "";
      var url = affiliateUrl(program, target);
      if (url === null) {
        // No partner link configured yet: keep a working non-affiliate link
        // instead of leaving a dead placeholder.
        if (target) {
          card.setAttribute("href", target);
          card.setAttribute("rel", "noopener");
          card.setAttribute("target", "_blank");
          card.removeAttribute("aria-disabled");
        } else {
          card.setAttribute("aria-disabled", "true");
          card.setAttribute("title", "Link is not available yet");
          card.addEventListener("click", function (event) {
            event.preventDefault();
          });
        }
        return;
      }
      card.setAttribute("href", url);
      card.setAttribute("rel", "sponsored nofollow noopener");
      card.setAttribute("target", "_blank");
      card.removeAttribute("aria-disabled");
    });
  }

  function markYear() {
    var node = document.getElementById("year");
    if (node) {
      node.textContent = String(new Date().getFullYear());
    }
  }

  function init() {
    wireDealCards();
    markYear();
    var consent = getConsent();
    if (consent === "all") {
      injectWidget();
    } else {
      showWidgetFallback();
      if (consent === null) showConsentBanner();
    }
  }

  document.addEventListener("click", function (event) {
    var target = event.target.closest ? event.target.closest("[data-cookie-reset]") : null;
    if (target) {
      event.preventDefault();
      resetConsent();
    }
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

(function(){
  var toggle=document.querySelector("[data-menu-toggle]");
  var nav=document.querySelector("[data-nav]");
  if(toggle && nav){
    function closeMenu(){toggle.setAttribute("aria-expanded","false");nav.classList.remove("is-open");}
    toggle.addEventListener("click",function(){
      var open=toggle.getAttribute("aria-expanded")==="true";
      toggle.setAttribute("aria-expanded",open?"false":"true");
      if(open){nav.classList.remove("is-open");}else{nav.classList.add("is-open");}
    });
    nav.querySelectorAll("a").forEach(function(link){link.addEventListener("click",closeMenu);});
    document.addEventListener("keydown",function(event){if(event.key==="Escape"){closeMenu();}});
  }
})();
