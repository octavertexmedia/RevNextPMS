// RevNext landing — looping interactive hero demos with animated mouse pointer

(function () {
  const REDUCE = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const IDLE_RESUME_MS = 12000;
  const CURSOR_MOVE_MS = 520;

  function inr(n) {
    return '₹' + Math.round(n).toLocaleString('en-IN');
  }

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  function showToast(root, message, selector) {
    const el = root.querySelector(selector || '[data-hero-toast]');
    if (!el) return;
    el.textContent = message;
    el.hidden = false;
    clearTimeout(el._toastTimer);
    el._toastTimer = setTimeout(() => {
      el.hidden = true;
    }, 1600);
  }

  function pulse(el) {
    if (!el) return;
    el.classList.remove('is-demo-pulse');
    void el.offsetWidth;
    el.classList.add('is-demo-pulse');
  }

  function selectOnly(nodes, active) {
    nodes.forEach((n) => n.classList.toggle('is-demo-selected', n === active));
  }

  function createDemoCursor(root) {
    let host = root;
    const stage = root.closest('.dawn-split-preview, .dawn-sol-preview-wrap, .dawn-sol-preview-body');
    if (stage) host = stage;

    if (getComputedStyle(host).position === 'static') {
      host.style.position = 'relative';
    }

    let cursor = host.querySelector(':scope > .ui-hero-cursor');
    if (!cursor) {
      cursor = document.createElement('div');
      cursor.className = 'ui-hero-cursor';
      cursor.setAttribute('aria-hidden', 'true');
      cursor.innerHTML =
        '<svg class="ui-hero-cursor-arrow" viewBox="0 0 24 24" width="28" height="28" fill="none">' +
        '<path d="M4.5 3.2l15.2 8.05c.7.37.55 1.4-.22 1.55l-6.3 1.25-2.7 6.55c-.3.72-1.35.6-1.45-.18L4.5 3.2z" fill="#0f172a" stroke="#fff" stroke-width="1.4" stroke-linejoin="round"/>' +
        '</svg>' +
        '<span class="ui-hero-cursor-ripple"></span>';
      host.appendChild(cursor);
    }

    let lastHover = null;

    function clearHover() {
      if (lastHover) {
        lastHover.classList.remove('is-demo-hover');
        lastHover = null;
      }
    }

    function setVisible(on) {
      cursor.classList.toggle('is-visible', !!on);
      if (!on) {
        cursor.classList.remove('is-clicking', 'is-pressing');
        clearHover();
      }
    }

    async function moveTo(el) {
      if (!el || !host.contains(el)) return;
      const hostRect = host.getBoundingClientRect();
      const rect = el.getBoundingClientRect();
      const x = rect.left - hostRect.left + Math.min(rect.width * 0.55, Math.max(12, rect.width / 2));
      const y = rect.top - hostRect.top + Math.min(rect.height * 0.55, Math.max(10, rect.height / 2));
      setVisible(true);
      cursor.style.transform = 'translate(' + x + 'px, ' + y + 'px)';
      clearHover();
      el.classList.add('is-demo-hover');
      lastHover = el;
      await sleep(CURSOR_MOVE_MS);
    }

    async function click(el) {
      if (!el) return;
      await moveTo(el);
      cursor.classList.add('is-pressing', 'is-clicking');
      await sleep(140);
      cursor.classList.remove('is-pressing');
      await sleep(180);
      cursor.classList.remove('is-clicking');
    }

    // Park near top-left of demo on start
    cursor.style.transform = 'translate(24px, 24px)';

    return { el: cursor, moveTo, click, setVisible, clearHover };
  }

  function createLooper(root, buildSteps, opts) {
    const options = Object.assign({ gap: 700, resumeMs: IDLE_RESUME_MS }, opts || {});
    const cursor = createDemoCursor(root);
    let stopped = false;
    let paused = false;
    let generation = 0;
    let resumeTimer = null;

    function pauseForUser() {
      paused = true;
      generation += 1;
      cursor.setVisible(false);
      clearTimeout(resumeTimer);
      resumeTimer = setTimeout(() => {
        paused = false;
        loop();
      }, options.resumeMs);
    }

    root.addEventListener(
      'pointerdown',
      () => {
        pauseForUser();
      },
      { capture: true }
    );

    async function runStep(step) {
      if (step.target) {
        await cursor.click(step.target);
      } else if (step.hover) {
        await cursor.moveTo(step.hover);
      }
      if (typeof step.fn === 'function') {
        await step.fn();
      }
    }

    async function loop() {
      const gen = ++generation;
      while (!stopped && gen === generation) {
        if (paused || document.hidden) {
          cursor.setVisible(false);
          await sleep(400);
          continue;
        }
        if (REDUCE) {
          await sleep(4000);
          continue;
        }
        cursor.setVisible(true);
        const steps = buildSteps(cursor);
        for (const step of steps) {
          if (stopped || paused || gen !== generation) return;
          try {
            await runStep(step);
          } catch (_) {
            /* ignore demo step errors */
          }
          await sleep(step.wait || options.gap);
        }
        await sleep(options.gap);
      }
    }

    if (!REDUCE) {
      const start = () => {
        if ('IntersectionObserver' in window) {
          const io = new IntersectionObserver(
            (entries) => {
              entries.forEach((entry) => {
                if (entry.isIntersecting) {
                  loop();
                  io.disconnect();
                }
              });
            },
            { threshold: 0.2 }
          );
          io.observe(root);
        } else {
          loop();
        }
      };
      start();
    }

    return { pauseForUser, cursor };
  }

  /* ---------------- POS ---------------- */
  function initPos(root) {
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

    let cart = [];
    let modeLabel = 'Table 3';

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
      const total = cart.reduce((s, i) => s + i.price * i.qty, 0);
      subtotalEl.textContent = inr(total);
      totalEl.textContent = inr(total);
      if (headEl) headEl.textContent = 'Current order · ' + modeLabel;
      if (emptyEl) emptyEl.hidden = cart.length > 0;
      if (holdBtn) holdBtn.disabled = !cart.length;
      if (payBtn) payBtn.disabled = !cart.length;
    }

    function setMode(btn) {
      modeBtns.forEach((b) => b.classList.remove('is-active'));
      btn.classList.add('is-active');
      modeLabel = btn.getAttribute('data-label') || 'Ticket';
      if (headEl) headEl.textContent = 'Current order · ' + modeLabel;
      pulse(btn);
    }

    function addItem(name, price) {
      const existing = cart.find((item) => item.name === name);
      if (existing) existing.qty += 1;
      else cart.push({ name, price, qty: 1 });
      const btn = menuBtns.find((b) => b.getAttribute('data-name') === name);
      pulse(btn);
      render();
    }

    function clearCart() {
      cart = [];
      render();
    }

    function pay() {
      if (!cart.length || !successEl) return;
      const paid = cart.reduce((s, i) => s + i.price * i.qty, 0);
      const count = cart.reduce((n, i) => n + i.qty, 0);
      if (successMetaEl) {
        successMetaEl.textContent = modeLabel + ' closed · ' + inr(paid) + ' · ' + count + ' items';
      }
      successEl.hidden = false;
      clearCart();
    }

    function resetTicket() {
      if (successEl) successEl.hidden = true;
      clearCart();
    }

    modeBtns.forEach((btn) => {
      btn.addEventListener('click', () => {
        setMode(btn);
        if (toastEl) {
          toastEl.textContent = btn.textContent.trim() + ' selected';
          toastEl.hidden = false;
          clearTimeout(toastEl._t);
          toastEl._t = setTimeout(() => {
            toastEl.hidden = true;
          }, 1400);
        }
      });
    });

    menuBtns.forEach((btn) => {
      btn.addEventListener('click', () => {
        addItem(btn.getAttribute('data-name'), Number(btn.getAttribute('data-price') || 0));
      });
    });

    if (linesEl) {
      linesEl.addEventListener('click', (e) => {
        const line = e.target.closest('[data-pos-line]');
        if (!line) return;
        const index = Number(line.getAttribute('data-pos-line'));
        const item = cart[index];
        if (!item) return;
        if (item.qty > 1) item.qty -= 1;
        else cart.splice(index, 1);
        render();
      });
    }

    if (holdBtn) {
      holdBtn.addEventListener('click', () => {
        if (!cart.length) return;
        const held = cart.reduce((s, i) => s + i.price * i.qty, 0);
        clearCart();
        if (toastEl) {
          toastEl.textContent = 'Ticket held · ' + inr(held);
          toastEl.hidden = false;
          clearTimeout(toastEl._t);
          toastEl._t = setTimeout(() => {
            toastEl.hidden = true;
          }, 1600);
        }
      });
    }

    if (payBtn) payBtn.addEventListener('click', pay);
    if (resetBtn) resetBtn.addEventListener('click', resetTicket);

    const modes = ['dine', 'takeaway', 'delivery'];
    let modeIdx = 0;

    createLooper(root, () => {
      const mode = modes[modeIdx % modes.length];
      modeIdx += 1;
      const modeBtn = modeBtns.find((b) => b.getAttribute('data-mode') === mode) || modeBtns[0];
      const picks =
        mode === 'delivery'
          ? [
              ['Combo Meal', 399],
              ['Cold Coffee', 99],
            ]
          : mode === 'takeaway'
            ? [
                ['Veg Burger', 149],
                ['Brownie', 129],
              ]
            : [
                ['Margherita', 299],
                ['Veg Burger', 149],
                ['Cold Coffee', 99],
              ];

      return [
        {
          wait: 350,
          fn: async () => resetTicket(),
        },
        {
          target: modeBtn,
          wait: 450,
          fn: async () => setMode(modeBtn),
        },
        ...picks.map(([name, price]) => {
          const btn = menuBtns.find((b) => b.getAttribute('data-name') === name);
          return {
            target: btn,
            wait: 480,
            fn: async () => addItem(name, price),
          };
        }),
        {
          target: payBtn,
          wait: 1400,
          fn: async () => pay(),
        },
        {
          target: resetBtn,
          wait: 900,
          fn: async () => resetTicket(),
        },
      ];
    });

    render();
  }

  /* ---------------- PMS ---------------- */
  function initPms(root) {
    const navBtns = Array.from(root.querySelectorAll('[data-pms-nav] button'));
    const title = root.querySelector('[data-pms-title]');
    const arrivals = Array.from(root.querySelectorAll('[data-pms-arrivals] tr'));
    const hkBtns = Array.from(root.querySelectorAll('[data-pms-hk] button'));
    const folio = root.querySelector('[data-pms-folio]');
    const newBtn = root.querySelector('[data-pms-new]');
    const arrivalsStat = root.querySelector('[data-stat="arrivals"]');
    const inhouseStat = root.querySelector('[data-stat="inhouse"]');
    const hkStat = root.querySelector('[data-stat="hk"]');

    function setNav(name) {
      navBtns.forEach((b) => b.classList.toggle('on', b.getAttribute('data-nav') === name));
      if (title) title.textContent = name === 'Dashboard' ? 'Front desk board' : name;
      const active = navBtns.find((b) => b.classList.contains('on'));
      pulse(active);
    }

    function checkIn(row) {
      const badge = row.querySelector('[data-guest-status]');
      if (!badge) return;
      badge.className = 'ui-badge ok';
      badge.textContent = 'Checked in';
      selectOnly(arrivals, row);
      pulse(row);
      if (arrivalsStat) arrivalsStat.textContent = String(Math.max(0, Number(arrivalsStat.textContent) - 1));
      if (inhouseStat) inhouseStat.textContent = String(Number(inhouseStat.textContent) + 1);
      showToast(root, 'Guest checked in');
    }

    function cycleHk(btn) {
      const status = btn.querySelector('[data-hk-status]');
      if (!status) return;
      const cycle = [
        { cls: 'dirty', label: 'Dirty' },
        { cls: 'insp', label: 'Inspect' },
        { cls: 'clean', label: 'Clean' },
        { cls: 'occ', label: 'Occupied' },
      ];
      const idx = cycle.findIndex((c) => status.classList.contains(c.cls));
      const next = cycle[(idx + 1) % cycle.length];
      status.className = next.cls;
      status.textContent = next.label;
      pulse(btn);
      if (hkStat && next.cls === 'clean') {
        hkStat.textContent = String(Math.max(0, Number(hkStat.textContent) - 1));
      }
    }

    navBtns.forEach((btn) => btn.addEventListener('click', () => setNav(btn.getAttribute('data-nav'))));
    arrivals.forEach((row) => row.addEventListener('click', () => checkIn(row)));
    hkBtns.forEach((btn) => btn.addEventListener('click', () => cycleHk(btn)));
    if (newBtn) {
      newBtn.addEventListener('click', () => {
        pulse(newBtn);
        showToast(root, 'Reservation draft opened');
      });
    }

    let guestIdx = 0;
    createLooper(root, () => {
      const row = arrivals[guestIdx % arrivals.length];
      guestIdx += 1;
      const arrivalsNav = navBtns.find((b) => b.getAttribute('data-nav') === 'Arrivals');
      const hkNav = navBtns.find((b) => b.getAttribute('data-nav') === 'Housekeeping');
      const dashNav = navBtns.find((b) => b.getAttribute('data-nav') === 'Dashboard');
      const dirty = hkBtns.find((b) => b.querySelector('.dirty')) || hkBtns[0];
      return [
        { target: arrivalsNav, wait: 400, fn: async () => setNav('Arrivals') },
        { target: row, wait: 500, fn: async () => checkIn(row) },
        { target: hkNav, wait: 400, fn: async () => setNav('Housekeeping') },
        { hover: folio, wait: 350, fn: async () => pulse(folio) },
        {
          target: dirty,
          wait: 500,
          fn: async () => {
            cycleHk(dirty);
            showToast(root, 'Room status updated');
          },
        },
        { target: dashNav, wait: 500, fn: async () => setNav('Dashboard') },
      ];
    });
  }

  /* ---------------- Channel Manager ---------------- */
  function initChannelManager(root) {
    const navBtns = Array.from(root.querySelectorAll('[data-cm-nav] button'));
    const title = root.querySelector('[data-cm-title]');
    const kicker = root.querySelector('[data-cm-kicker]');
    const rows = Array.from(root.querySelectorAll('[data-cm-rows] tr'));

    function setNav(name) {
      navBtns.forEach((b) => b.classList.toggle('on', b.getAttribute('data-nav') === name));
      if (title) {
        title.textContent =
          name === 'Channels' ? 'Channel health' : name === 'Inventory' ? 'Inventory push' : name;
      }
      pulse(navBtns.find((b) => b.classList.contains('on')));
    }

    function syncRow(row) {
      const status = row.querySelector('[data-cm-status]');
      const inv = row.querySelector('[data-cm-inv]');
      if (status) {
        status.className = 'ui-badge info';
        status.textContent = 'Syncing';
      }
      selectOnly(rows, row);
      pulse(row);
      setTimeout(() => {
        if (status) {
          status.className = 'ui-badge ok';
          status.textContent = 'Live';
        }
        if (inv) inv.textContent = 'Synced just now';
        if (kicker) kicker.textContent = 'ARI sync · live';
        showToast(root, row.cells[0].textContent.trim() + ' live');
      }, 700);
    }

    navBtns.forEach((btn) => btn.addEventListener('click', () => setNav(btn.getAttribute('data-nav'))));
    rows.forEach((row) => row.addEventListener('click', () => syncRow(row)));

    let rowIdx = 0;
    createLooper(root, () => {
      const row = rows[rowIdx % rows.length];
      rowIdx += 1;
      const channels = navBtns.find((b) => b.getAttribute('data-nav') === 'Channels');
      const inventory = navBtns.find((b) => b.getAttribute('data-nav') === 'Inventory');
      const rates = navBtns.find((b) => b.getAttribute('data-nav') === 'Rates');
      return [
        { target: channels, wait: 350, fn: async () => setNav('Channels') },
        {
          wait: 300,
          fn: async () => {
            if (kicker) kicker.textContent = 'ARI sync · pushing';
          },
        },
        { target: row, wait: 1100, fn: async () => syncRow(row) },
        { target: inventory, wait: 400, fn: async () => setNav('Inventory') },
        { target: rates, wait: 400, fn: async () => setNav('Rates') },
        { target: channels, wait: 450, fn: async () => setNav('Channels') },
      ];
    });
  }

  /* ---------------- Booking Engine ---------------- */
  function initBooking(root) {
    const rates = Array.from(root.querySelectorAll('[data-book-rates] .ui-rate'));
    const continueBtn = root.querySelector('[data-book-continue]');
    const success = root.querySelector('[data-book-success]');
    const successMeta = root.querySelector('[data-book-success-meta]');
    const resetBtn = root.querySelector('[data-book-reset]');
    let selected = rates[0];

    function selectRate(btn) {
      rates.forEach((r) => r.classList.toggle('on', r === btn));
      selected = btn;
      const nightly = Number(btn.getAttribute('data-rate') || 0);
      if (continueBtn) continueBtn.textContent = 'Continue · ' + inr(nightly * 2);
      pulse(btn);
    }

    function complete() {
      if (!selected || !success) return;
      if (successMeta) {
        successMeta.textContent =
          (selected.getAttribute('data-label') || 'Stay') +
          ' · 2 nights · ' +
          continueBtn.textContent.replace('Continue · ', '');
      }
      success.hidden = false;
      pulse(continueBtn);
    }

    rates.forEach((btn) => btn.addEventListener('click', () => selectRate(btn)));
    if (continueBtn) continueBtn.addEventListener('click', complete);
    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        success.hidden = true;
        selectRate(rates[0]);
      });
    }

    let i = 0;
    createLooper(root, () => {
      const rate = rates[i % rates.length];
      i += 1;
      return [
        {
          wait: 250,
          fn: async () => {
            if (success) success.hidden = true;
          },
        },
        { target: rate, wait: 450, fn: async () => selectRate(rate) },
        { target: continueBtn, wait: 1200, fn: async () => complete() },
        {
          target: resetBtn,
          wait: 800,
          fn: async () => {
            if (success) success.hidden = true;
            selectRate(rates[0]);
          },
        },
      ];
    });
  }

  /* ---------------- Website builder ---------------- */
  function initWebsite(root) {
    const rooms = Array.from(root.querySelectorAll('[data-site-rooms] button'));
    const cta = root.querySelector('[data-site-cta]');
    const headline = root.querySelector('[data-site-headline]');
    const lead = root.querySelector('[data-site-lead]');
    const headlines = [
      ['Wake up to the harbour', 'Boutique stays in Colaba — book direct and save.'],
      ['Sea-facing suites this weekend', 'Free breakfast · late checkout on suite nights.'],
      ['Stay 3, pay 2 is live', 'Direct guests keep the offer — no OTA cut.'],
    ];

    rooms.forEach((btn) => {
      btn.addEventListener('click', () => {
        selectOnly(rooms, btn);
        pulse(btn);
        showToast(root, btn.querySelector('strong').textContent + ' highlighted');
      });
    });
    if (cta) {
      cta.addEventListener('click', () => {
        pulse(cta);
        showToast(root, 'Opening Booking Engine…');
      });
    }

    let i = 0;
    createLooper(root, () => {
      const copy = headlines[i % headlines.length];
      const room = rooms[i % rooms.length];
      i += 1;
      return [
        {
          hover: headline,
          wait: 500,
          fn: async () => {
            if (headline) headline.textContent = copy[0];
            if (lead) lead.textContent = copy[1];
            pulse(headline);
          },
        },
        {
          target: room,
          wait: 450,
          fn: async () => {
            selectOnly(rooms, room);
            pulse(room);
          },
        },
        {
          target: cta,
          wait: 700,
          fn: async () => {
            pulse(cta);
            showToast(root, 'Book now → direct checkout');
          },
        },
      ];
    });
  }

  /* ---------------- Mobile apps ---------------- */
  function initMobile(root) {
    const rows = Array.from(root.querySelectorAll('[data-app-row]'));
    const rooms = Array.from(root.querySelectorAll('[data-app-rooms] button'));

    function flipArrival(row) {
      const badge = row.querySelector('[data-app-badge]');
      if (!badge) return;
      badge.className = 'ui-badge ok';
      badge.textContent = 'In-house';
      selectOnly(rows, row);
      pulse(row);
      showToast(root, 'Checked in from mobile');
    }

    function flipRoom(btn) {
      const status = btn.querySelector('[data-hk-status]');
      if (!status) return;
      status.className = 'clean';
      status.textContent = 'Clean';
      pulse(btn);
      showToast(root, 'Room ' + btn.getAttribute('data-room') + ' cleaned');
    }

    rows.forEach((row) => row.addEventListener('click', () => flipArrival(row)));
    rooms.forEach((btn) => btn.addEventListener('click', () => flipRoom(btn)));

    let i = 0;
    createLooper(root, () => {
      const row = rows[i % rows.length];
      const room = rooms[i % rooms.length];
      i += 1;
      return [
        { target: row, wait: 500, fn: async () => flipArrival(row) },
        { target: room, wait: 550, fn: async () => flipRoom(room) },
        {
          wait: 450,
          fn: async () => {
            const badge = row.querySelector('[data-app-badge]');
            if (badge && i % 2 === 0) {
              badge.className = 'ui-badge warn';
              badge.textContent = 'Due';
            }
          },
        },
      ];
    });
  }

  /* ---------------- B2B ---------------- */
  function initB2b(root) {
    const rows = Array.from(root.querySelectorAll('[data-b2b-rows] tr'));
    const bookBtn = root.querySelector('[data-b2b-book]');
    let selected = rows[0];

    function selectRow(row) {
      selected = row;
      selectOnly(rows, row);
      pulse(row);
    }

    function reserve() {
      if (!selected) return;
      const allot = selected.querySelector('[data-b2b-allot]');
      let n = Number(allot.textContent);
      if (n > 0) {
        n -= 1;
        allot.textContent = String(n);
        selected.setAttribute('data-allotment', String(n));
      }
      pulse(bookBtn);
      showToast(root, 'Allotment reserved · ' + selected.cells[0].textContent.trim());
    }

    rows.forEach((row) => row.addEventListener('click', () => selectRow(row)));
    if (bookBtn) bookBtn.addEventListener('click', reserve);

    let i = 0;
    createLooper(root, () => {
      const row = rows[i % rows.length];
      i += 1;
      return [
        { target: row, wait: 450, fn: async () => selectRow(row) },
        { target: bookBtn, wait: 600, fn: async () => reserve() },
        {
          wait: 700,
          fn: async () => {
            const allot = row.querySelector('[data-b2b-allot]');
            if (!row.getAttribute('data-allotment-base')) {
              row.setAttribute('data-allotment-base', String(Number(allot.textContent) + 1));
            }
            if (Number(allot.textContent) <= 0) {
              allot.textContent = row.getAttribute('data-allotment-base');
            }
          },
        },
      ];
    });
  }

  /* ---------------- OTA listing ---------------- */
  function initOta(root) {
    const steps = Array.from(root.querySelectorAll('[data-ota-step]'));

    function paint(activeIndex) {
      steps.forEach((li, idx) => {
        li.classList.remove('done', 'active');
        const strong = li.querySelector('strong');
        if (idx < activeIndex) {
          li.classList.add('done');
          if (strong) strong.textContent = idx === 2 ? 'Live' : 'Done';
        } else if (idx === activeIndex) {
          li.classList.add('active');
          if (strong) strong.textContent = 'In review';
          pulse(li);
        } else if (strong) {
          strong.textContent = idx === steps.length - 1 ? 'Next' : 'Queued';
        }
      });
      showToast(root, steps[Math.min(activeIndex, steps.length - 1)].querySelector('span').textContent.trim());
    }

    steps.forEach((li, idx) => li.addEventListener('click', () => paint(idx)));

    let i = 3;
    createLooper(root, () => {
      const idx = i % steps.length;
      i += 1;
      return [{ target: steps[idx], wait: 1100, fn: async () => paint(idx) }];
    });
  }

  /* ---------------- Google Hotel Ads ---------------- */
  function initGha(root) {
    const query = root.querySelector('[data-gha-query]');
    const deal = root.querySelector('[data-gha-deal]');
    const success = root.querySelector('[data-gha-success]');
    const resetBtn = root.querySelector('[data-gha-reset]');
    const serp = root.querySelector('[data-gha-serp]');
    const queries = ['hotels in mumbai colaba', 'boutique hotel colaba', 'harbour view hotel mumbai'];

    async function typeQuery(text) {
      if (!query) return;
      query.textContent = '';
      for (let c = 0; c < text.length; c += 1) {
        query.textContent += text[c];
        await sleep(28);
      }
      pulse(query);
    }

    function openDeal() {
      if (success) success.hidden = false;
      pulse(deal);
      pulse(serp);
    }

    if (deal) deal.addEventListener('click', openDeal);
    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        if (success) success.hidden = true;
      });
    }

    let i = 0;
    createLooper(root, () => {
      const q = queries[i % queries.length];
      i += 1;
      return [
        {
          wait: 200,
          fn: async () => {
            if (success) success.hidden = true;
          },
        },
        { hover: query, wait: 100, fn: async () => typeQuery(q) },
        { hover: serp, wait: 450, fn: async () => pulse(serp) },
        { target: deal, wait: 1100, fn: async () => openDeal() },
        {
          target: resetBtn,
          wait: 800,
          fn: async () => {
            if (success) success.hidden = true;
          },
        },
      ];
    });
  }

  /* ---------------- Aggregator ---------------- */
  function initAggregator(root) {
    const rows = Array.from(root.querySelectorAll('[data-agg-rows] tr'));
    const title = root.querySelector('[data-agg-title]');
    const count = root.querySelector('[data-agg-count]');

    function selectRow(row) {
      selectOnly(rows, row);
      pulse(row);
      const action = row.querySelector('[data-agg-action]');
      if (action) {
        action.textContent = 'Selected';
        action.className = 'ui-badge ok';
      }
      rows.forEach((r) => {
        if (r === row) return;
        const a = r.querySelector('[data-agg-action]');
        if (!a) return;
        if (r.getAttribute('data-agg-row') === '2') {
          a.textContent = '3 left';
          a.className = 'ui-badge warn';
        } else {
          a.textContent = 'Available';
          a.className = 'ui-badge ok';
        }
      });
      showToast(root, row.cells[0].textContent.trim() + ' selected');
    }

    rows.forEach((row) => {
      row.addEventListener('click', () => selectRow(row));
      const action = row.querySelector('[data-agg-action]');
      if (action) {
        action.addEventListener('click', (e) => {
          e.stopPropagation();
          selectRow(row);
        });
      }
    });

    let i = 0;
    createLooper(root, () => {
      const row = rows[i % rows.length];
      i += 1;
      const action = row.querySelector('[data-agg-action]');
      return [
        {
          wait: 300,
          fn: async () => {
            if (title) title.textContent = 'Search · Mumbai · 2 nights';
            if (count) count.textContent = '24 stays';
          },
        },
        { target: action || row, wait: 550, fn: async () => selectRow(row) },
        {
          hover: count,
          wait: 500,
          fn: async () => {
            if (count) count.textContent = 'Match ready';
            pulse(count);
          },
        },
      ];
    });
  }

  /* ---------------- Tours ---------------- */
  function initTours(root) {
    const rows = Array.from(root.querySelectorAll('[data-tours-rows] tr'));
    const bookBtn = root.querySelector('[data-tours-book]');
    let selected = rows[0];

    function selectRow(row) {
      selected = row;
      selectOnly(rows, row);
      pulse(row);
    }

    function book() {
      if (!selected) return;
      const seats = selected.querySelector('[data-tours-seats]');
      let n = Number(seats.textContent);
      if (n > 0) {
        n -= 2;
        if (n < 0) n = 0;
        seats.textContent = String(n);
      }
      pulse(bookBtn);
      showToast(root, '2 seats held · ' + selected.cells[0].textContent.trim());
    }

    rows.forEach((row) => {
      if (!row.getAttribute('data-seats-base')) {
        row.setAttribute('data-seats-base', row.querySelector('[data-tours-seats]').textContent);
      }
      row.addEventListener('click', () => selectRow(row));
    });
    if (bookBtn) bookBtn.addEventListener('click', book);

    let i = 0;
    createLooper(root, () => {
      const row = rows[i % rows.length];
      i += 1;
      return [
        { target: row, wait: 450, fn: async () => selectRow(row) },
        { target: bookBtn, wait: 600, fn: async () => book() },
        {
          wait: 700,
          fn: async () => {
            const seats = row.querySelector('[data-tours-seats]');
            if (Number(seats.textContent) <= 2) {
              seats.textContent = row.getAttribute('data-seats-base');
            }
          },
        },
      ];
    });
  }

  const registry = {
    'cloud-pos': initPos,
    'cloud-pms': initPms,
    'channel-manager': initChannelManager,
    'booking-engine': initBooking,
    'website-builder': initWebsite,
    'mobile-apps': initMobile,
    'b2b-network': initB2b,
    'ota-listing': initOta,
    'google-hotel-ads': initGha,
    'hotel-aggregator': initAggregator,
    tours: initTours,
  };

  function boot() {
    document.querySelectorAll('[data-hero-demo]').forEach((root) => {
      const key = root.getAttribute('data-hero-demo');
      const init = registry[key];
      if (init) init(root);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
