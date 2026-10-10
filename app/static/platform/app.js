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

  /* ---------- Обучение: копирование кода ---------- */

  function initCodeCopy() {
    document.querySelectorAll('[data-code]').forEach(function (block) {
      var pre = block.querySelector('pre');
      if (!pre) return;
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'code-copy';
      btn.textContent = 'Копировать';
      btn.addEventListener('click', function () {
        copyText(pre.innerText.replace(/\n$/, '')).then(function () {
          btn.textContent = 'Скопировано';
          setTimeout(function () { btn.textContent = 'Копировать'; }, 2000);
        }, function () { toast('Не удалось скопировать — выделите код вручную'); });
      });
      block.appendChild(btn);
    });
  }

  /* ---------- Обучение: последний открытый урок ---------- */

  // Хранится только в этом браузере — для кнопки «Продолжить».
  function readLast(course) {
    try { return localStorage.getItem('learning:last:' + course) || ''; } catch (e) { return ''; }
  }

  function saveLast(course, lesson) {
    try { localStorage.setItem('learning:last:' + course, lesson); } catch (e) { /* приватный режим */ }
  }

  function initLessonPage() {
    var page = document.querySelector('[data-lesson-page]');
    if (!page) return;
    saveLast(page.getAttribute('data-course'), page.getAttribute('data-lesson-page'));

    // На десктопе программа всегда раскрыта; текущий урок — в зоне видимости.
    var nav = page.querySelector('[data-lesson-nav]');
    if (nav && window.matchMedia('(min-width: 1024px)').matches) {
      nav.open = true;
      var current = nav.querySelector('[aria-current="page"]');
      var scroller = page.querySelector('.lesson-nav');
      if (current && scroller) scroller.scrollTop = current.offsetTop - scroller.clientHeight / 3;
    }
  }

  // Страницы курса и темы: кнопка «Продолжить» ведёт к последнему открытому уроку.
  function initContinue() {
    var root = document.querySelector('[data-course]:not([data-lesson-page])');
    var source = document.getElementById('course-lessons');
    if (!root || !source) return;
    var lessons = JSON.parse(source.textContent);
    var last = readLast(root.getAttribute('data-course'));
    if (!lessons[last]) return;

    var cta = root.querySelector('[data-continue]');
    var topicCta = root.querySelector('[data-topic-continue]');
    if (topicCta && topicCta.getAttribute('data-topic').split(' ').indexOf(last) === -1) topicCta = null;
    [cta, topicCta].forEach(function (btn) {
      if (!btn) return;
      btn.href = lessons[last].url;
      btn.textContent = 'Продолжить: ' + lessons[last].title;
    });
  }

  /* ---------- Обучение: активный пункт содержания ---------- */

  function initLessonToc() {
    var links = document.querySelectorAll('.lesson-toc--side a');
    if (!links.length) return;
    var byId = {};
    links.forEach(function (a) { byId[decodeURIComponent(a.hash.slice(1))] = a; });
    var headings = Array.prototype.filter.call(
      document.querySelectorAll('.lesson-prose h2[id], .lesson-prose h3[id]'),
      function (h) { return byId[h.id]; }
    );
    var current = null;
    var ticking = false;

    // Активен последний заголовок, который уже ушёл под шапку (+ небольшой запас).
    function update() {
      ticking = false;
      var offset = 120;
      var active = null;
      headings.forEach(function (h) {
        if (h.getBoundingClientRect().top <= offset) active = h;
      });
      if (active === current) return;
      if (current) byId[current.id].classList.remove('is-active');
      if (active) byId[active.id].classList.add('is-active');
      current = active;
    }

    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
    }, { passive: true });
    update();
  }

  /* ---------- Тема ---------- */

  function initTheme() {
    var btn = document.querySelector('[data-theme-toggle]');
    var root = document.documentElement;
    var meta = document.querySelector('meta[name="theme-color"]');

    function apply(theme) {
      root.setAttribute('data-theme', theme);
      if (meta) meta.setAttribute('content', theme === 'light' ? '#f4f4f1' : '#0c0c0e');
      if (btn) {
        btn.setAttribute('aria-label', theme === 'light' ? 'Включить тёмную тему' : 'Включить светлую тему');
        btn.setAttribute('title', btn.getAttribute('aria-label'));
      }
    }

    apply(root.getAttribute('data-theme') === 'light' ? 'light' : 'dark');
    if (!btn) return;
    btn.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
      apply(next);
      try { localStorage.setItem('theme', next); } catch (e) {}
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.documentElement.classList.add('js');
    initTheme();
    initStages();
    initTabs();
    initSearch();
    initSwatches();
    initPrompt();
    initCodeCopy();
    initLessonPage();
    initContinue();
    initLessonToc();
  });
})();
