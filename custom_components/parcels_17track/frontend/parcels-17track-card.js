/* Parcels for 17TRACK – dashboard card (no build step, no dependencies). */
const DOMAIN = "parcels_17track";
const CARD_VERSION = "1.0.0";

const STATES = {
  alert: { icon: "mdi:alert-circle-outline", color: "var(--error-color, #db4437)" },
  undelivered: { icon: "mdi:package-variant-remove", color: "var(--error-color, #db4437)" },
  expired: { icon: "mdi:clock-alert-outline", color: "var(--disabled-text-color, #9e9e9e)" },
  out_for_delivery: { icon: "mdi:truck-fast-outline", color: "var(--warning-color, #ff9800)" },
  ready_to_be_picked_up: { icon: "mdi:storefront-outline", color: "var(--warning-color, #ff9800)" },
  in_transit: { icon: "mdi:truck-delivery-outline", color: "var(--info-color, #2196f3)" },
  not_found: { icon: "mdi:magnify", color: "var(--disabled-text-color, #9e9e9e)" },
  delivered: { icon: "mdi:package-variant-closed-check", color: "var(--success-color, #43a047)" },
};

const TEXT = {
  en: {
    alert: "Problem", undelivered: "Delivery failed", expired: "Expired",
    out_for_delivery: "Out for delivery", ready_to_be_picked_up: "Ready for pickup",
    in_transit: "In transit", not_found: "No data yet", delivered: "Delivered",
    s_in_transit: "In transit", s_ready: "Ready", s_problems: "Problems", s_delivered: "Delivered",
    empty: "No open parcels", delivered_list: "{n} delivered", archive_hint: "archived after delivery",
    number: "Tracking number", name: "Name (optional)", add: "Add", added: "Added – it shows up in a moment.",
    stale: "17TRACK hasn't answered since {t}.", refresh: "Refresh", open: "Open in 17TRACK",
    missing: "Entity not found: {e}",
  },
  de: {
    alert: "Problem", undelivered: "Zustellung fehlgeschlagen", expired: "Abgelaufen",
    out_for_delivery: "Heute in Zustellung", ready_to_be_picked_up: "Abholbereit",
    in_transit: "Unterwegs", not_found: "Noch keine Daten", delivered: "Zugestellt",
    s_in_transit: "Unterwegs", s_ready: "Abholbereit", s_problems: "Probleme", s_delivered: "Zugestellt",
    empty: "Keine offenen Sendungen", delivered_list: "{n} zugestellt", archive_hint: "werden nach Zustellung archiviert",
    number: "Sendungsnummer", name: "Bezeichnung (optional)", add: "Hinzufügen", added: "Hinzugefügt – erscheint gleich.",
    stale: "17TRACK antwortet seit {t} nicht.", refresh: "Aktualisieren", open: "In 17TRACK öffnen",
    missing: "Entität nicht gefunden: {e}",
  },
};

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

class Parcels17TrackCard extends HTMLElement {
  static getConfigForm() {
    return {
      schema: [
        { name: "entity", required: true, selector: { entity: { filter: { integration: DOMAIN, domain: "sensor" } } } },
        { name: "title", selector: { text: {} } },
        {
          type: "grid",
          name: "",
          schema: [
            { name: "show_delivered", selector: { boolean: {} } },
            { name: "show_add_form", selector: { boolean: {} } },
          ],
        },
      ],
      computeLabel: (s) =>
        ({
          entity: "Parcel sensor (Open parcels)",
          title: "Title",
          show_delivered: "Show delivered parcels",
          show_add_form: "Show add-parcel form",
        })[s.name],
    };
  }

  static getStubConfig(hass) {
    const entity = Object.keys(hass.states).find(
      (id) => id.startsWith("sensor.") && hass.states[id].attributes.integration === DOMAIN
    );
    return { entity: entity || "", show_delivered: true, show_add_form: true };
  }

  setConfig(config) {
    if (!config || !config.entity) throw new Error("Please choose the 'Open parcels' sensor (entity).");
    this._config = { show_delivered: true, show_add_form: true, ...config };
    this._built = false;
    this._lastState = undefined;
    if (this._hass) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    const state = hass.states[this._config?.entity];
    if (!this._built || state !== this._lastState) {
      this._lastState = state;
      this._render();
    }
  }

  getCardSize() {
    const n = (this._lastState?.attributes?.parcels || []).length;
    return 2 + Math.min(n, 6) + (this._config?.show_add_form ? 1 : 0);
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  _lang() {
    const l = this._hass?.locale?.language || this._hass?.language || "en";
    return l.toLowerCase().startsWith("de") ? "de" : "en";
  }

  _t(key, vars = {}) {
    let s = (TEXT[this._lang()] || TEXT.en)[key] ?? TEXT.en[key] ?? key;
    for (const [k, v] of Object.entries(vars)) s = s.replace(`{${k}}`, v);
    return s;
  }

  _ago(ts) {
    if (!ts) return "";
    const diff = (new Date(ts).getTime() - Date.now()) / 1000;
    if (Number.isNaN(diff)) return "";
    const rtf = new Intl.RelativeTimeFormat(this._hass?.locale?.language || this._lang(), { numeric: "auto" });
    const abs = Math.abs(diff);
    if (abs < 3600) return rtf.format(Math.round(diff / 60), "minute");
    if (abs < 86400) return rtf.format(Math.round(diff / 3600), "hour");
    return rtf.format(Math.round(diff / 86400), "day");
  }

  _time(ts) {
    if (!ts) return "–";
    return new Date(ts).toLocaleTimeString(this._hass?.locale?.language || undefined, { hour: "2-digit", minute: "2-digit" });
  }

  _build() {
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `
      <style>
        :host { --p17-gap: 12px; }
        ha-card { padding: 16px; }
        .head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
        .title { font-size: 1.15em; font-weight: 500; flex: 1; }
        .updated { color: var(--secondary-text-color); font-size: 0.85em; display: flex; align-items: center; gap: 2px; }
        .icon-btn { background: none; border: none; color: var(--secondary-text-color); cursor: pointer; padding: 6px; border-radius: 50%; display: inline-flex; }
        .icon-btn:hover { background: var(--secondary-background-color); color: var(--primary-text-color); }
        .icon-btn.spin ha-icon { animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .stats { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 4px; }
        .stat { display: flex; align-items: center; gap: 6px; padding: 6px 10px; border-radius: 999px;
                background: var(--secondary-background-color); font-size: 0.9em; }
        .stat b { font-size: 1.05em; }
        .stat ha-icon { --mdc-icon-size: 18px; }
        .stat span { color: var(--secondary-text-color); }
        .list { display: flex; flex-direction: column; margin-top: 8px; }
        .row { display: grid; grid-template-columns: 40px 1fr auto; gap: var(--p17-gap); align-items: center;
               padding: 8px 4px; border-radius: 12px; color: inherit; text-decoration: none; }
        .row:hover { background: var(--secondary-background-color); }
        .bubble { width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; position: relative; overflow: hidden; }
        .bubble::before { content: ""; position: absolute; inset: 0; background: currentColor; opacity: 0.15; }
        .bubble ha-icon { --mdc-icon-size: 22px; position: relative; }
        .main { min-width: 0; }
        .name { font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .status { font-size: 0.9em; }
        .status .ago, .info { color: var(--secondary-text-color); }
        .info { font-size: 0.85em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .open { color: var(--secondary-text-color); --mdc-icon-size: 18px; }
        .empty { display: flex; align-items: center; gap: 10px; color: var(--secondary-text-color); padding: 12px 4px; }
        .empty ha-icon { color: var(--success-color, #43a047); }
        .warn { margin-top: 8px; padding: 8px 12px; border-radius: 10px; font-size: 0.9em; display: flex; gap: 8px; align-items: center;
                background: rgba(255, 152, 0, 0.12); color: var(--primary-text-color); }
        .warn ha-icon { color: var(--warning-color, #ff9800); --mdc-icon-size: 18px; }
        details { margin-top: 6px; }
        summary { cursor: pointer; color: var(--secondary-text-color); font-size: 0.9em; padding: 6px 4px; list-style: none; display: flex; align-items: center; gap: 6px; }
        summary::-webkit-details-marker { display: none; }
        summary ha-icon { --mdc-icon-size: 18px; transition: transform 0.2s; }
        details[open] summary ha-icon.chev { transform: rotate(90deg); }
        .done { display: grid; grid-template-columns: 24px 1fr auto; gap: 8px; align-items: center; padding: 4px; font-size: 0.9em;
                color: inherit; text-decoration: none; border-radius: 8px; }
        .done:hover { background: var(--secondary-background-color); }
        .done ha-icon { --mdc-icon-size: 18px; color: var(--success-color, #43a047); }
        .done .ago { color: var(--secondary-text-color); }
        form { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
        input { flex: 1 1 140px; min-width: 0; font: inherit; color: var(--primary-text-color); background: var(--secondary-background-color);
                border: none; border-radius: 10px; padding: 10px 12px; outline: none; }
        input:focus { box-shadow: 0 0 0 2px var(--primary-color); }
        button.add { font: inherit; font-weight: 500; border: none; border-radius: 10px; padding: 10px 16px; cursor: pointer;
                     background: var(--primary-color); color: var(--text-primary-color, #fff); display: inline-flex; align-items: center; gap: 6px; }
        button.add:disabled { opacity: 0.5; cursor: default; }
        .msg { font-size: 0.85em; color: var(--secondary-text-color); margin-top: 6px; min-height: 1em; }
        .msg.err { color: var(--error-color, #db4437); }
      </style>
      <ha-card>
        <div class="head">
          <div class="title"></div>
          <div class="updated"></div>
          <button class="icon-btn refresh" title=""><ha-icon icon="mdi:refresh"></ha-icon></button>
        </div>
        <div class="stats"></div>
        <div class="warnbox"></div>
        <div class="list"></div>
        <div class="donebox"></div>
        <div class="formbox">
          <form>
            <input name="number" autocomplete="off" spellcheck="false" />
            <input name="name" autocomplete="off" />
            <button class="add" type="submit"><ha-icon icon="mdi:plus"></ha-icon><span></span></button>
          </form>
          <div class="msg"></div>
        </div>
      </ha-card>`;
    const root = this.shadowRoot;
    root.querySelector(".refresh").addEventListener("click", () => this._refresh());
    root.querySelector("form").addEventListener("submit", (ev) => {
      ev.preventDefault();
      this._add();
    });
    this._built = true;
  }

  _render() {
    if (!this._config || !this._hass) return;
    if (!this._built) this._build();
    const root = this.shadowRoot;
    const st = this._hass.states[this._config.entity];

    root.querySelector(".title").textContent = this._config.title || "";
    root.querySelector(".title").style.display = this._config.title ? "" : "none";
    root.querySelector(".refresh").title = this._t("refresh");
    root.querySelector("input[name=number]").placeholder = this._t("number");
    root.querySelector("input[name=name]").placeholder = this._t("name");
    root.querySelector("button.add span").textContent = this._t("add");
    root.querySelector(".formbox").style.display = this._config.show_add_form ? "" : "none";

    if (!st) {
      root.querySelector(".list").innerHTML = `<div class="warn"><ha-icon icon="mdi:alert"></ha-icon>${esc(this._t("missing", { e: this._config.entity }))}</div>`;
      return;
    }
    const a = st.attributes;
    const parcels = Array.isArray(a.parcels) ? a.parcels : [];
    const open = parcels.filter((p) => p.state !== "delivered");
    const done = parcels.filter((p) => p.state === "delivered");

    root.querySelector(".updated").innerHTML = a.last_success
      ? `<ha-icon icon="mdi:clock-outline" style="--mdc-icon-size:14px"></ha-icon>&nbsp;${esc(this._time(a.last_success))}`
      : "";

    const stat = (icon, color, n, label, always) =>
      n || always
        ? `<div class="stat"><ha-icon icon="${icon}" style="color:${color}"></ha-icon><b>${n}</b><span>${esc(label)}</span></div>`
        : "";
    root.querySelector(".stats").innerHTML =
      stat(STATES.in_transit.icon, STATES.in_transit.color, a.in_transit || 0, this._t("s_in_transit"), true) +
      stat(STATES.ready_to_be_picked_up.icon, STATES.ready_to_be_picked_up.color, a.ready_for_pickup || 0, this._t("s_ready")) +
      stat(STATES.alert.icon, STATES.alert.color, a.problems || 0, this._t("s_problems")) +
      stat(STATES.delivered.icon, STATES.delivered.color, a.delivered || 0, this._t("s_delivered"), true);

    const staleAfter = (a.scan_interval || 30) * 2.5 * 60 * 1000;
    const stale = a.last_success && Date.now() - new Date(a.last_success).getTime() > staleAfter;
    root.querySelector(".warnbox").innerHTML = stale
      ? `<div class="warn"><ha-icon icon="mdi:cloud-alert"></ha-icon>${esc(this._t("stale", { t: this._time(a.last_success) }))}</div>`
      : "";

    root.querySelector(".list").innerHTML = open.length
      ? open.map((p) => this._row(p)).join("")
      : `<div class="empty"><ha-icon icon="mdi:check-circle-outline"></ha-icon>${esc(this._t("empty"))}</div>`;

    const doneBox = root.querySelector(".donebox");
    if (this._config.show_delivered && done.length) {
      const wasOpen = doneBox.querySelector("details")?.open;
      doneBox.innerHTML = `<details ${wasOpen ? "open" : ""}><summary><ha-icon class="chev" icon="mdi:chevron-right"></ha-icon>${esc(
        this._t("delivered_list", { n: done.length })
      )}</summary>${done
        .map(
          (p) => `<a class="done" href="${esc(p.url)}" target="_blank" rel="noreferrer" title="${esc(this._t("open"))}">
            <ha-icon icon="mdi:check-circle-outline"></ha-icon><span>${esc(p.name)}</span><span class="ago">${esc(this._ago(p.timestamp))}</span></a>`
        )
        .join("")}</details>`;
    } else {
      doneBox.innerHTML = "";
    }
  }

  _row(p) {
    const s = STATES[p.state] || STATES.not_found;
    const label = TEXT[this._lang()][p.state] || p.status || "";
    const info = [p.info_text, p.location].filter(Boolean).join(" · ");
    const ago = this._ago(p.timestamp);
    return `<a class="row" href="${esc(p.url)}" target="_blank" rel="noreferrer" title="${esc(p.tracking_number)}">
      <div class="bubble" style="color:${s.color}"><ha-icon icon="${s.icon}"></ha-icon></div>
      <div class="main">
        <div class="name">${esc(p.name)}</div>
        <div class="status"><span style="color:${s.color}">${esc(label)}</span>${ago ? `<span class="ago"> · ${esc(ago)}</span>` : ""}</div>
        ${info ? `<div class="info">${esc(info)}</div>` : ""}
      </div>
      <ha-icon class="open" icon="mdi:open-in-new"></ha-icon>
    </a>`;
  }

  async _refresh() {
    const btn = this.shadowRoot.querySelector(".refresh");
    btn.classList.add("spin");
    try {
      await this._hass.callService(DOMAIN, "refresh", {});
    } finally {
      btn.classList.remove("spin");
    }
  }

  async _add() {
    const root = this.shadowRoot;
    const num = root.querySelector("input[name=number]");
    const name = root.querySelector("input[name=name]");
    const msg = root.querySelector(".msg");
    const btn = root.querySelector("button.add");
    const number = num.value.replace(/\s+/g, "");
    if (!number) return;
    btn.disabled = true;
    msg.className = "msg";
    msg.textContent = "";
    try {
      const data = { tracking_number: number };
      if (name.value.trim()) data.name = name.value.trim();
      await this._hass.callService(DOMAIN, "add_parcel", data);
      num.value = "";
      name.value = "";
      msg.textContent = this._t("added");
    } catch (err) {
      msg.className = "msg err";
      msg.textContent = err?.message || String(err);
    } finally {
      btn.disabled = false;
    }
  }
}

if (!customElements.get("parcels-17track-card")) {
  customElements.define("parcels-17track-card", Parcels17TrackCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "parcels-17track-card",
    name: "17TRACK Parcels",
    description: "Your 17TRACK parcels with status, latest event and an add-parcel form.",
    preview: true,
    documentationURL: "https://github.com/benkl/ha-parcels-17track",
  });
  console.info(`%c PARCELS-17TRACK-CARD %c ${CARD_VERSION} `, "color:#fff;background:#2196f3;font-weight:700", "color:#2196f3");
}
