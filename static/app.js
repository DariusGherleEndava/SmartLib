
(function () {
  const form = document.getElementById('queryForm');
  const input = document.getElementById('q');
  const out = document.getElementById('out');
  const loading = document.getElementById('loading');
  const errorBox = document.getElementById('errorBox');
  const submitBtn = document.getElementById('submitBtn');
  const clearBtn = document.getElementById('clearBtn');
  const copyBtn = document.getElementById('copyBtn');
  const saveSnippetBtn = document.getElementById('saveSnippetBtn');
  const historyList = document.getElementById('historyList');
  const clearHistoryBtn = document.getElementById('clearHistoryBtn');
  const themeToggle = document.getElementById('themeToggle');

  document.getElementById('year').textContent = new Date().getFullYear();

  const DARK_KEY = 'br_dark';
  if (localStorage.getItem(DARK_KEY) === '1') {
    document.body.classList.add('dark');
    themeToggle.textContent = 'Light mode';
  }

  themeToggle.addEventListener('click', () => {
    const isDark = document.body.classList.toggle('dark');
    localStorage.setItem(DARK_KEY, isDark ? '1' : '0');
    themeToggle.textContent = isDark ? 'Light mode' : 'Dark mode';
  });

  // Istoric cautari simple (prompt + raspuns)
  const HIST_KEY = 'br_history';
  function loadHistory() {
    try {
      return JSON.parse(localStorage.getItem(HIST_KEY) || '[]');
    } catch {
      return [];
    }
  }
  function saveHistory(arr) {
    localStorage.setItem(HIST_KEY, JSON.stringify(arr.slice(0, 50)));
  }
  function renderHistory() {
    const items = loadHistory();
    historyList.innerHTML = '';
    if (!items.length) {
      historyList.innerHTML = '<li class="text-sm text-gray-400">Istoricul este gol.</li>';
      return;
    }
    items.forEach((it, idx) => {
      const li = document.createElement('li');
      li.className = 'border rounded-xl p-3 hover:bg-gray-50 cursor-pointer';
      li.innerHTML = `
        <div class="text-xs text-gray-500 mb-1">#${idx + 1}</div>
        <div class="text-sm font-medium line-clamp-2">${escapeHTML(it.prompt)}</div>
        <div class="text-xs text-gray-500 mt-1 line-clamp-2">${escapeHTML(it.answer)}</div>
      `;
      li.addEventListener('click', () => {
        input.value = it.prompt;
        out.textContent = it.answer;
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
      historyList.appendChild(li);
    });
  }
  renderHistory();

  clearHistoryBtn.addEventListener('click', () => {
    localStorage.removeItem(HIST_KEY);
    renderHistory();
  });

  clearBtn.addEventListener('click', () => {
    input.value = '';
    out.textContent = '';
    hideError();
  });

  copyBtn.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(out.textContent || '');
      flash(copyBtn, 'Copiat!');
    } catch {
      flash(copyBtn, 'Nu s-a putut copia');
    }
  });

  saveSnippetBtn.addEventListener('click', () => {
    const prompt = input.value.trim();
    const answer = (out.textContent || '').trim();
    if (!prompt || !answer) {
      flash(saveSnippetBtn, 'Nimic de salvat');
      return;
    }
    const items = loadHistory();
    items.unshift({ prompt, answer, ts: Date.now() });
    saveHistory(items);
    renderHistory();
    flash(saveSnippetBtn, 'Salvat');
  });

  // Submit
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    await doQuery();
  });

  //  Ctrl+Enter
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      doQuery();
    }
  });

  async function doQuery() {
    hideError();
    const userInput = input.value.trim();
    if (!userInput) {
      showError('Te rugam scrie un prompt inainte de a trimite.');
      return;
    }
    setLoading(true);
    out.textContent = '';

    try {
      const res = await fetch('/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_input: userInput })
      });
      if (!res.ok) {
        const err = await safeJson(res);
        throw new Error(err?.error || ('Eroare HTTP ' + res.status));
      }
      const data = await res.json();
      const text = data?.recommendation || 'Nu a venit niciun raspuns.';
      out.textContent = text;

      // Salveaza automat in istoric (doar promptul, raspunsul curent)
      const items = loadHistory();
      items.unshift({ prompt: userInput, answer: text, ts: Date.now() });
      saveHistory(items);
      renderHistory();
    } catch (err) {
      showError(err.message || 'A aparut o eroare neasteptata.');
    } finally {
      setLoading(false);
    }
  }

  function setLoading(flag) {
    submitBtn.disabled = flag;
    loading.classList.toggle('hidden', !flag);
  }

  function showError(msg) {
    errorBox.textContent = msg;
    errorBox.classList.remove('hidden');
  }
  function hideError() {
    errorBox.classList.add('hidden');
    errorBox.textContent = '';
  }

  function flash(el, msg) {
    const orig = el.textContent;
    el.textContent = msg;
    el.disabled = true;
    setTimeout(() => {
      el.textContent = orig;
      el.disabled = false;
    }, 900);
  }

  function escapeHTML(str) {
    return (str || '').replace(/[&<>"']/g, s => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[s]
    ));
  }

  async function safeJson(res) {
    try { return await res.json(); } catch { return null; }
  }
})();
