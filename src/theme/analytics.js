// Busuanzi — анонимный счётчик без регистрации
(function() {
  // Добавляем скрипт Busuanzi
  const script = document.createElement('script');
  script.async = true;
  script.src = '//busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js';
  document.head.appendChild(script);
  
  // Ждём загрузки скрипта
  script.onload = function() {
    // Добавляем счётчики в футер
    const footer = document.createElement('div');
    footer.style.cssText = 'text-align: center; margin: 2rem 0; padding-top: 1rem; border-top: 1px solid var(--table-border-color); font-size: 0.85rem; opacity: 0.7;';
    
    footer.innerHTML = `
      <span id="busuanzi_container_site_pv">
        👁 <span id="busuanzi_value_site_pv"></span> просмотров
      </span>
      &nbsp;|&nbsp;
      <span id="busuanzi_container_site_uv">
        👤 <span id="busuanzi_value_site_uv"></span> читателей
      </span>
      &nbsp;|&nbsp;
      <span id="busuanzi_container_page_pv">
        📖 Эта глава: <span id="busuanzi_value_page_pv"></span> просмотров
      </span>
    `;
    
    document.querySelector('.content').appendChild(footer);
  };
})();
