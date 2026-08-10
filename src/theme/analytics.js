// Busuanzi — анонимная статистика книги
(() => {
  const SCRIPT_ID = "busuanzi-script";
  const FOOTER_CLASS = "book-statistics";

  if (document.getElementById(SCRIPT_ID)) {
    return;
  }

  const script = document.createElement("script");

  script.id = SCRIPT_ID;
  script.async = true;
  script.src =
    "https://busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js";

  script.onload = () => {
    const content = document.querySelector(".content");

    if (!content || content.querySelector(`.${FOOTER_CLASS}`)) {
      return;
    }

    const statistics = document.createElement("div");

    statistics.className = FOOTER_CLASS;

    statistics.innerHTML = `
      <span id="busuanzi_container_site_pv" hidden>
        <span aria-hidden="true">👁</span>
        <span id="busuanzi_value_site_pv"></span>
        просмотров
      </span>

      <span class="book-statistics-separator" aria-hidden="true">
        ·
      </span>

      <span id="busuanzi_container_site_uv" hidden>
        <span aria-hidden="true">👤</span>
        <span id="busuanzi_value_site_uv"></span>
        посетителей
      </span>

      <span class="book-statistics-separator" aria-hidden="true">
        ·
      </span>

      <span id="busuanzi_container_page_pv" hidden>
        <span aria-hidden="true">📖</span>
        эта глава:
        <span id="busuanzi_value_page_pv"></span>
      </span>
    `;

    content.appendChild(statistics);

    // Busuanzi заполняет значения асинхронно.
    // Показываем только контейнеры, для которых значение действительно появилось.
    const containers = statistics.querySelectorAll(
      '[id^="busuanzi_container_"]',
    );

    containers.forEach((container) => {
      const value = container.querySelector('[id^="busuanzi_value_"]');

      if (!value) {
        return;
      }

      const observer = new MutationObserver(() => {
        if (value.textContent?.trim()) {
          container.hidden = false;
          observer.disconnect();
        }
      });

      observer.observe(value, {
        childList: true,
        characterData: true,
        subtree: true,
      });
    });
  };

  script.onerror = () => {
    // Статистика не должна влиять на работу книги.
    script.remove();
  };

  document.head.appendChild(script);
})();
