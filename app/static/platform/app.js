/* Поведение оболочки платформы. Без зависимостей; всё основное работает и без JS. */
(function () {
  'use strict';

  /* ---------- Уведомление ---------- */

  var toastEl;
  var toastTimer;

  function toast(message) {
    if (!toastEl) {
      toastEl = document.createElement('div');
      toastEl.className = 'toast';
      toastEl.setAttribute('role', 'status');
      toastEl.setAttribute('aria-live', 'polite');
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = message;
    toastEl.classList.add('is-visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove('is-visible'); }, 2200);
  }

  /* ---------- Копирование ---------- */

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
      var area = document.createElement('textarea');
      area.value = text;
      area.setAttribute('readonly', '');
      area.style.position = 'fixed';
      area.style.opacity = '0';
      document.body.appendChild(area);
      area.select();
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      document.body.removeChild(area);
      ok ? resolve() : reject(new Error('copy failed'));
    });
  }

  /* ---------- Масштабирование демонстраций ---------- */

  function fitStage(stage) {
    var w = parseFloat(stage.style.getPropertyValue('--stage-w'));
    if (!w || !stage.clientWidth) return;
    var scale = Math.min(stage.clientWidth / w, 1);
    stage.style.setProperty('--stage-scale', scale.toFixed(4));
  }

  function initStages(root) {
    var stages = (root || document).querySelectorAll('[data-stage]');
    if (!stages.length) return;
    if ('ResizeObserver' in window) {
      var ro = new ResizeObserver(function (entries) {
        entries.forEach(function (entry) { fitStage(entry.target); });
      });
      stages.forEach(function (s) { ro.observe(s); });
    } else {
      var fitAll = function () { stages.forEach(fitStage); };
      window.addEventListener('resize', fitAll);
      fitAll();
    }
  }

  /* ---------- Переключатель демонстраций ---------- */

  function initTabs() {
    document.querySelectorAll('[data-tabs]').forEach(function (wrap) {
      var tabs = Array.prototype.slice.call(wrap.querySelectorAll('[role="tab"]'));
      if (!tabs.length) return;

      function select(tab, focus) {
        tabs.forEach(function (t) {
          var selected = t === tab;
          t.setAttribute('aria-selected', selected ? 'true' : 'false');
          t.tabIndex = selected ? 0 : -1;
          var panel = document.getElementById(t.getAttribute('aria-controls'));
          if (panel) panel.hidden = !selected;
          if (selected && panel) panel.querySelectorAll('[data-stage]').forEach(fitStage);
        });
        if (focus) tab.focus();
        var url = new URL(window.location.href);
        url.searchParams.set('demo', tab.dataset.variant);
        history.replaceState(history.state, '', url);
      }

      tabs.forEach(function (tab, i) {
        tab.addEventListener('click', function (e) {
          e.preventDefault();
          select(tab, false);
        });
        tab.addEventListener('keydown', function (e) {
          var next = null;
          if (e.key === 'ArrowRight') next = tabs[(i + 1) % tabs.length];
          if (e.key === 'ArrowLeft') next = tabs[(i - 1 + tabs.length) % tabs.length];
          if (e.key === 'Home') next = tabs[0];
          if (e.key === 'End') next = tabs[tabs.length - 1];
          if (next) { e.preventDefault(); select(next, true); }
        });
      });
    });
  }

  /* ---------- Поиск по каталогу ---------- */

  function normalize(text) {
    return (text || '').toLowerCase().replace(/ё/g, 'е').replace(/\s+/g, ' ').trim();
  }

  function initSearch() {
    var form = document.querySelector('[data-search-form]');
    if (!form) return;
    var input = form.querySelector('input[type="search"]');
    var hiddenKind = form.querySelector('[data-kind-input]');
    if (hiddenKind) hiddenKind.remove();
    var items = Array.prototype.slice.call(document.querySelectorAll('[data-search-item]'));
    var filters = Array.prototype.slice.call(document.querySelectorAll('[data-filters] [data-kind]'));
    var status = document.querySelector('[data-search-status]');
    var note = status.textContent.split(' · ').slice(1).join(' · ');
    var empty = document.querySelector('[data-search-empty]');
    var reset = document.querySelectorAll('[data-search-reset]');
    var current = filters.filter(function (f) { return f.getAttribute('aria-current') === 'true'; })[0];
    var kind = current ? current.getAttribute('data-kind') : '';

    function apply() {
      var words = normalize(input.value).split(' ').filter(Boolean);
      var count = 0;
      items.forEach(function (item) {
        var text = item.getAttribute('data-search-item');
        var match = words.every(function (w) { return text.indexOf(w) !== -1; }) &&
          (!kind || item.getAttribute('data-kind') === kind);
        item.hidden = !match;
        if (match) count++;
      });
      filters.forEach(function (f) {
        if (f.getAttribute('data-kind') === kind) f.setAttribute('aria-current', 'true');
        else f.removeAttribute('aria-current');
      });
      status.textContent = 'Показано: ' + count + ' из ' + items.length + (note ? ' · ' + note : '');
      empty.hidden = count !== 0;
      var url = new URL(window.location.href);
      if (words.length) url.searchParams.set('q', input.value.trim());
      else url.searchParams.delete('q');
      if (kind) url.searchParams.set('kind', kind);
      else url.searchParams.delete('kind');
      history.replaceState(history.state, '', url);
    }

    input.addEventListener('input', apply);
    form.addEventListener('submit', function (e) { e.preventDefault(); apply(); });
    filters.forEach(function (f) {
      f.addEventListener('click', function (e) {
        e.preventDefault();
        kind = f.getAttribute('data-kind');
        apply();
      });
    });
    reset.forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        input.value = '';
        kind = '';
        apply();
        input.focus();
      });
    });
  }

  /* ---------- Копирование HEX ---------- */

  function initSwatches() {
    document.querySelectorAll('[data-copy]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var value = btn.getAttribute('data-copy');
        copyText(value).then(function () {
          toast('Скопировано: ' + value);
        }, function () {
          toast('Не удалось скопировать. Код цвета: ' + value);
        });
      });
    });
  }

  /* ---------- Промпт ---------- */

  function initPrompt() {
    var btn = document.querySelector('[data-copy-prompt]');
    if (!btn) return;
    var area = document.getElementById(btn.getAttribute('data-copy-prompt'));
    var status = document.querySelector('[data-copy-status]');
    var label = btn.querySelector('[data-label]');
    var initial = label.textContent;
    var timer;

    btn.addEventListener('click', function () {
      copyText(area.value).then(function () {
        status.className = 'copy-status copy-status--ok';
        status.textContent = 'Промпт скопирован в буфер обмена. Вставьте его в чат с ИИ вместе с задачей проекта.';
        label.textContent = 'Скопировано';
        clearTimeout(timer);
        timer = setTimeout(function () { label.textContent = initial; }, 2500);
      }, function () {
        status.className = 'copy-status copy-status--fail';
        status.textContent = 'Браузер не дал скопировать автоматически. Текст выделен — нажмите Ctrl+C (⌘+C на Mac) или скачайте файл.';
        area.focus();
        area.select();
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.documentElement.classList.add('js');
    initStages();
    initTabs();
    initSearch();
    initSwatches();
    initPrompt();
  });
})();
