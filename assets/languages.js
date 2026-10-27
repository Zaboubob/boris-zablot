// Preserve homepage section anchors when switching language; links work without JS.
document.querySelectorAll('[data-language-home]').forEach(link => {
  if (window.location.hash) link.hash = window.location.hash;
});
