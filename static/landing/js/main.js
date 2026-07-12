// RevNext landing — Dawn Concierge interactions

document.addEventListener('DOMContentLoaded', function () {
  const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
  const mobileMenu = document.querySelector('.mobile-menu');

  if (mobileMenuBtn && mobileMenu) {
    mobileMenuBtn.addEventListener('click', function () {
      const open = mobileMenu.classList.toggle('is-open');
      mobileMenu.hidden = !open;
      mobileMenuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  const header = document.querySelector('.dawn-header');
  if (header) {
    const onScroll = () => {
      header.classList.toggle('is-scrolled', window.scrollY > 24);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (!href || href === '#') return;
      const target = document.querySelector(href);
      if (!target) return;
      e.preventDefault();
      const offset = 80;
      const top = target.getBoundingClientRect().top + window.pageYOffset - offset;
      window.scrollTo({ top, behavior: 'smooth' });
      if (mobileMenu && mobileMenu.classList.contains('is-open')) {
        mobileMenu.classList.remove('is-open');
        mobileMenu.hidden = true;
      }
    });
  });

  const revealEls = document.querySelectorAll('.dawn-reveal');
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );
    revealEls.forEach((el) => io.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add('is-visible'));
  }

  initPosHeroDemo();
});

function initPosHeroDemo() {
  const root = document.querySelector('[data-pos-demo]');
  if (!root) return;

  const linesEl = root.querySelector('[data-pos-lines]');
  const emptyEl = root.querySelector('[data-pos-empty]');
  const subtotalEl = root.querySelector('[data-pos-subtotal]');
  const totalEl = root.querySelector('[data-pos-total]');
  const headEl = root.querySelector('[data-pos-ticket-head]');
  const toastEl = root.querySelector('[data-pos-toast]');
  const successEl = root.querySelector('[data-pos-success]');
  const successMetaEl = root.querySelector('[data-pos-success-meta]');
  const holdBtn = root.querySelector('[data-pos-hold]');
  const payBtn = root.querySelector('[data-pos-pay]');
  const resetBtn = root.querySelector('[data-pos-reset]');
  const modeBtns = Array.from(root.querySelectorAll('.ui-pos-mode'));
  const menuBtns = Array.from(root.querySelectorAll('[data-pos-menu] button'));

  /** @type {{ name: string, price: number, qty: number }[]} */
  let cart = [
    { name: 'Margherita', price: 299, qty: 1 },
    { name: 'Veg Burger', price: 149, qty: 1 },
  ];
  let modeLabel = 'Table 3';
  let toastTimer = null;

  const inr = (n) => '₹' + Math.round(n).toLocaleString('en-IN');

  function cartTotal() {
    return cart.reduce((sum, item) => sum + item.price * item.qty, 0);
  }

  function showToast(message) {
    if (!toastEl) return;
    toastEl.textContent = message;
    toastEl.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toastEl.hidden = true;
    }, 1600);
  }

  function setActionsEnabled(enabled) {
    if (holdBtn) holdBtn.disabled = !enabled;
    if (payBtn) payBtn.disabled = !enabled;
  }

  function render() {
    if (!linesEl || !subtotalEl || !totalEl) return;

    linesEl.innerHTML = '';
    cart.forEach((item, index) => {
      const li = document.createElement('li');
      li.setAttribute('data-pos-line', String(index));
      li.title = 'Tap to remove one';
      const label = document.createElement('span');
      if (item.qty > 1) {
        const qty = document.createElement('span');
        qty.className = 'ui-pos-qty';
        qty.textContent = item.qty + '×';
        label.appendChild(qty);
      }
      label.appendChild(document.createTextNode(item.name));
      const amount = document.createElement('strong');
      amount.textContent = inr(item.price * item.qty);
      li.appendChild(label);
      li.appendChild(amount);
      linesEl.appendChild(li);
    });

    const total = cartTotal();
    subtotalEl.textContent = inr(total);
    totalEl.textContent = inr(total);
    if (headEl) headEl.textContent = 'Current order · ' + modeLabel;
    if (emptyEl) emptyEl.hidden = cart.length > 0;
    setActionsEnabled(cart.length > 0);
  }

  function addItem(name, price) {
    const existing = cart.find((item) => item.name === name);
    if (existing) {
      existing.qty += 1;
    } else {
      cart.push({ name, price, qty: 1 });
    }
    render();
  }

  function removeOne(index) {
    const item = cart[index];
    if (!item) return;
    if (item.qty > 1) {
      item.qty -= 1;
    } else {
      cart.splice(index, 1);
    }
    render();
  }

  modeBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      modeBtns.forEach((b) => b.classList.remove('is-active'));
      btn.classList.add('is-active');
      modeLabel = btn.getAttribute('data-label') || 'Ticket';
      if (headEl) headEl.textContent = 'Current order · ' + modeLabel;
      showToast(btn.textContent.trim() + ' selected');
    });
  });

  menuBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      const name = btn.getAttribute('data-name');
      const price = Number(btn.getAttribute('data-price') || 0);
      if (!name || !price) return;
      addItem(name, price);
      btn.classList.add('is-pulse');
      window.setTimeout(() => btn.classList.remove('is-pulse'), 180);
    });
  });

  if (linesEl) {
    linesEl.addEventListener('click', (e) => {
      const line = e.target.closest('[data-pos-line]');
      if (!line || !linesEl.contains(line)) return;
      const index = Number(line.getAttribute('data-pos-line'));
      removeOne(index);
    });
  }

  if (holdBtn) {
    holdBtn.addEventListener('click', () => {
      if (!cart.length) return;
      const heldTotal = cartTotal();
      cart = [];
      render();
      showToast('Ticket held · ' + inr(heldTotal));
    });
  }

  if (payBtn) {
    payBtn.addEventListener('click', () => {
      if (!cart.length || !successEl) return;
      const paid = cartTotal();
      if (successMetaEl) {
        successMetaEl.textContent =
          modeLabel +
          ' closed · ' +
          inr(paid) +
          ' · ' +
          cart.reduce((n, i) => n + i.qty, 0) +
          ' items';
      }
      successEl.hidden = false;
      cart = [];
      render();
    });
  }

  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      if (successEl) successEl.hidden = true;
      cart = [];
      render();
      showToast('New ticket ready');
    });
  }

  render();
}
