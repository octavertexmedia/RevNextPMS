// RevNext landing — looping interactive hero demos for every product UI

(function () {
  const REDUCE = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const IDLE_RESUME_MS = 12000;

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

  function createLooper(root, buildSteps, opts) {
    const options = Object.assign({ gap: 900, resumeMs: IDLE_RESUME_MS }, opts || {});
    let stopped = false;
    let paused = false;
    let generation = 0;
    let resumeTimer = null;

    function pauseForUser() {
      paused = true;
      generation += 1;
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

    async function loop() {
      const gen = ++generation;
      while (!stopped && gen === generation) {
        if (paused || document.hidden) {
          await sleep(400);
          continue;
        }
        if (REDUCE) {
          await sleep(4000);
          continue;
        }
        const steps = buildSteps();
        for (const step of steps) {
          if (stopped || paused || gen !== generation) return;
          try {
            await step.fn();
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
            { threshold: 0.25 }
          );
          io.observe(root);
        } else {
          loop();
        }
      };
      start();
    }

    return { pauseForUser };
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
    let autoPlaying = false;

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
          wait: 500,
          fn: async () => {
            autoPlaying = true;
            resetTicket();
            setMode(modeBtn);
          },
        },
        ...picks.map(([name, price]) => ({
          wait: 700,
          fn: async () => addItem(name, price),
        })),
        {
          wait: 900,
          fn: async () => {
            pulse(payBtn);
          },
        },
        {
          wait: 1600,
          fn: async () => pay(),
        },
        {
          wait: 1400,
          fn: async () => {
            resetTicket();
            autoPlaying = false;
          },
        },
      ];
    });

    render();
    return { autoPlaying: () => autoPlaying };
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
      return [
        { wait: 700, fn: async () => setNav('Arrivals') },
        {
          wait: 900,
          fn: async () => {
            selectOnly(arrivals, row);
            pulse(row);
          },
        },
        { wait: 1000, fn: async () => checkIn(row) },
        {
          wait: 800,
          fn: async () => {
            setNav('Housekeeping');
            pulse(folio);
          },
        },
        {
          wait: 900,
          fn: async () => {
            const dirty = hkBtns.find((b) => b.querySelector('.dirty')) || hkBtns[0];
            cycleHk(dirty);
            showToast(root, 'Room status updated');
          },
        },
        { wait: 800, fn: async () => setNav('Dashboard') },
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
      return [
        { wait: 600, fn: async () => setNav('Channels') },
        {
          wait: 500,
          fn: async () => {
            if (kicker) kicker.textContent = 'ARI sync · pushing';
          },
        },
        { wait: 1200, fn: async () => syncRow(row) },
        { wait: 700, fn: async () => setNav('Inventory') },
        { wait: 700, fn: async () => setNav('Rates') },
        { wait: 700, fn: async () => setNav('Channels') },
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
          (selected.getAttribute('data-label') || 'Stay') + ' · 2 nights · ' + continueBtn.textContent.replace('Continue · ', '');
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
          wait: 400,
          fn: async () => {
            if (success) success.hidden = true;
          },
        },
        { wait: 800, fn: async () => selectRate(rate) },
        { wait: 700, fn: async () => pulse(continueBtn) },
        { wait: 1400, fn: async () => complete() },
        {
          wait: 1200,
          fn: async () => {
            if (success) success.hidden = true;
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
          wait: 700,
          fn: async () => {
            if (headline) headline.textContent = copy[0];
            if (lead) lead.textContent = copy[1];
            pulse(headline);
          },
        },
        {
          wait: 800,
          fn: async () => {
            selectOnly(rooms, room);
            pulse(room);
          },
        },
        {
          wait: 900,
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
        { wait: 800, fn: async () => flipArrival(row) },
        { wait: 900, fn: async () => flipRoom(room) },
        {
          wait: 700,
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
        { wait: 700, fn: async () => selectRow(row) },
        { wait: 900, fn: async () => reserve() },
        {
          wait: 1000,
          fn: async () => {
            const allot = row.querySelector('[data-b2b-allot]');
            const base = Number(row.getAttribute('data-allotment-base') || row.getAttribute('data-allotment') || allot.textContent);
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
    const states = [
      { cls: 'done', label: 'Done' },
      { cls: 'done', label: 'Live' },
      { cls: 'active', label: 'In review' },
      { cls: '', label: 'Queued' },
      { cls: '', label: 'Next' },
    ];

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
        } else {
          if (strong) strong.textContent = idx === steps.length - 1 ? 'Next' : 'Queued';
        }
      });
      showToast(root, steps[Math.min(activeIndex, steps.length - 1)].querySelector('span').textContent.trim());
    }

    steps.forEach((li, idx) => li.addEventListener('click', () => paint(idx)));

    let i = 3;
    createLooper(root, () => {
      const idx = i % steps.length;
      i += 1;
      return [{ wait: 1400, fn: async () => paint(idx) }];
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
      for (let i = 0; i < text.length; i += 1) {
        query.textContent += text[i];
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
          wait: 300,
          fn: async () => {
            if (success) success.hidden = true;
          },
        },
        { wait: 200, fn: async () => typeQuery(q) },
        { wait: 800, fn: async () => pulse(serp) },
        { wait: 900, fn: async () => openDeal() },
        {
          wait: 1400,
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
      if (action) action.addEventListener('click', (e) => {
        e.stopPropagation();
        selectRow(row);
      });
    });

    let i = 0;
    createLooper(root, () => {
      const row = rows[i % rows.length];
      i += 1;
      return [
        {
          wait: 600,
          fn: async () => {
            if (title) title.textContent = 'Search · Mumbai · 2 nights';
            if (count) count.textContent = '24 stays';
          },
        },
        { wait: 900, fn: async () => selectRow(row) },
        {
          wait: 800,
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
        { wait: 700, fn: async () => selectRow(row) },
        { wait: 900, fn: async () => book() },
        {
          wait: 1000,
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
