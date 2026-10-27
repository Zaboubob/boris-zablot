/* Native scrolling remains available without JavaScript. No automatic advance. */
document.querySelectorAll('[data-project-carousel]').forEach(carousel => {
  const track = carousel.querySelector('.project-track');
  const controls = carousel.querySelector('.project-carousel-controls');
  const previous = controls.querySelector('[data-previous]');
  const next = controls.querySelector('[data-next]');
  const count = carousel.querySelector('.project-carousel-count');
  const cards = [...track.querySelectorAll('.project-card')];
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const update = () => {
    const maximum = track.scrollWidth - track.clientWidth;
    controls.hidden = maximum <= 2;
    const step = cards[0]?.getBoundingClientRect().width + parseFloat(getComputedStyle(track).columnGap);
    const current = step ? Math.min(cards.length - 1, Math.round(track.scrollLeft / step)) : 0;
    count.textContent = `${current + 1} / ${cards.length}`;
  };
  const move = direction => {
    const card = track.querySelector('.project-card');
    if (!card) return;
    const step = card.getBoundingClientRect().width + parseFloat(getComputedStyle(track).columnGap);
    const current = Math.round(track.scrollLeft / step);
    const target = (current + direction + cards.length) % cards.length;
    track.scrollTo({left: target * step, behavior: reducedMotion.matches ? 'instant' : 'smooth'});
  };
  previous.addEventListener('click', () => move(-1));
  next.addEventListener('click', () => move(1));
  track.addEventListener('keydown', event => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    if (event.key === 'Home' || event.key === 'End') {
      track.scrollTo({left: event.key === 'Home' ? 0 : track.scrollWidth, behavior: reducedMotion.matches ? 'instant' : 'smooth'});
    } else move(event.key === 'ArrowLeft' ? -1 : 1);
  });
  track.addEventListener('scroll', update, {passive:true});
  new ResizeObserver(update).observe(track);
  update();
});
