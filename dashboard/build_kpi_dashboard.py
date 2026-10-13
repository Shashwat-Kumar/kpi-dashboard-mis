"""Sample 1 – KPI dashboard & MIS for 'Northwind Retail' (FICTIONAL D2C brand, SYNTHETIC data).
Generates synthetic customers/orders/spend, computes KPIs, renders dashboard PNG (1600x900) and 4-page PDF."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "common"))
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from style import *
mpl_setup()
rng = np.random.default_rng(42)
OUT = HERE
MONTHS = pd.period_range("2025-10", "2026-09", freq="M")
LBL = [m.strftime("%b %y") for m in MONTHS]
CH = ["Paid Social", "Search", "Marketplace", "Referral", "Organic"]
REG = ["North", "South", "West", "East"]
# ---------------- synthetic generation ----------------
# Simulate 24 months (Oct 2024 - Sep 2026) so the customer base is warm; report the last 12.
import warnings; warnings.filterwarnings("ignore")
NM = 24; R0 = 12
season = np.tile([1.25, 1.35, 1.05, 0.90, 0.85, 0.95, 0.95, 1.00, 1.00, 1.05, 1.10, 1.15], 2)  # Oct-Nov festive peak
growth = np.concatenate([np.linspace(0.90, 1.0, 12), np.linspace(1.0, 1.22, 12)])
base_new = {"Paid Social": 3100, "Search": 2200, "Marketplace": 1700, "Referral": 650, "Organic": 1200}
ch_growth = {"Paid Social": 1.0, "Search": 1.0, "Marketplace": 0.95, "Referral": 1.25, "Organic": 1.08}
cac_path = {"Paid Social": np.concatenate([np.linspace(500, 540, 12), np.linspace(540, 820, 12)]),
            "Search": np.concatenate([np.full(12, 465.0), np.linspace(470, 540, 12)]),
            "Marketplace": np.full(NM, 330.0), "Referral": np.full(NM, 360.0), "Organic": np.full(NM, 290.0)}
ret_m1 = {"Paid Social": 0.19, "Search": 0.24, "Marketplace": 0.16, "Referral": 0.31, "Organic": 0.28}
reg_p = {"North": 0.31, "South": 0.27, "West": 0.27, "East": 0.15}
reg_growth = {"North": 1.0, "South": 1.35, "West": 1.05, "East": 0.95}
reg_aov = {"North": 1.00, "South": 1.06, "West": 1.10, "East": 0.88}
ch_aov = {"Paid Social": 0.95, "Search": 1.02, "Marketplace": 0.90, "Referral": 1.08, "Organic": 1.05}
cust, spend = [], []
cid = 0
for mi in range(NM):
    for c in CH:
        n = int(base_new[c] * season[mi] * growth[mi] ** ch_growth[c] * rng.normal(1, 0.03))
        t = max(0, mi - R0) / 11
        w = np.array([reg_p[r] * reg_growth[r] ** t for r in REG]); w /= w.sum()
        regs = rng.choice(REG, n, p=w)
        cust.append(pd.DataFrame({"customer_id": np.arange(cid, cid + n), "acq_month": mi, "channel": c, "region": regs}))
        cid += n
        spend.append({"month": mi, "channel": c, "spend": n * cac_path[c][mi] * rng.normal(1, 0.02), "new_customers": n})
cust = pd.concat(cust, ignore_index=True); spend = pd.DataFrame(spend)
orders = []
loyalty = np.array([1.0 if m < R0 + 7 else 1.22 for m in range(NM)])  # loyalty programme launched May 2026
for mi in range(NM):
    for c in CH:
        sub = cust[(cust.acq_month <= mi) & (cust.channel == c)]
        k = (mi - sub.acq_month.values).astype(float)
        p = np.where(k == 0, 1.0, ret_m1[c] * np.maximum(k, 1) ** -0.5 * loyalty[mi] * season[mi] ** 0.5)
        active = sub[rng.random(len(sub)) < np.clip(p, 0, 1)]
        n_ord = 1 + rng.poisson(0.12, len(active))
        rep = active.loc[active.index.repeat(n_ord)]
        aov = 1380 * season[mi] ** 0.6 * np.array([reg_aov[r] for r in rep.region]) * ch_aov[c] * (1 + 0.004 * mi)
        val = rng.lognormal(np.log(aov) - 0.18, 0.6)
        orders.append(pd.DataFrame({"month": mi, "customer_id": rep.customer_id.values, "channel": c,
                                    "region": rep.region.values, "acq_month": rep.acq_month.values, "order_value": val.round(0)}))
orders = pd.concat(orders, ignore_index=True)
# keep reporting window only; re-index months to 0..11 (first-ever order month kept for repeat logic)
orders = orders[orders.month >= R0].copy(); orders["month"] -= R0; orders["acq_month"] -= R0
spend = spend[spend.month >= R0].copy(); spend["month"] -= R0
cust_all = cust; cust = cust[cust.acq_month >= R0].copy(); cust["acq_month"] -= R0
orders["order_id"] = np.arange(len(orders)) + 100000
orders["month_label"] = [str(MONTHS[m]) for m in orders.month]
# ---------------- KPIs ----------------
mk = orders.groupby("month").agg(revenue=("order_value", "sum"), orders=("order_id", "count"),
                                 active_customers=("customer_id", "nunique")).reset_index()
mk["aov"] = mk.revenue / mk.orders
sp = spend.groupby("month").agg(spend=("spend", "sum"), new_customers=("new_customers", "sum")).reset_index()
mk = mk.merge(sp, on="month"); mk["cac"] = mk.spend / mk.new_customers
ret = orders[orders.month > orders.acq_month].groupby("month").customer_id.nunique()
mk["repeat_rate"] = (ret.reindex(mk.month).fillna(0).values / mk.active_customers)
mk["month_label"] = [str(m) for m in MONTHS]
ch_rev = orders.groupby(["month", "channel"]).order_value.sum().unstack()[CH]
reg_rev = orders.groupby("region").order_value.sum()[REG]
reg_rev_h = orders.assign(h=np.where(orders.month < 6, "H1", "H2")).groupby(["region", "h"]).order_value.sum().unstack().loc[REG]
coh = orders.groupby(["acq_month", "month"]).customer_id.nunique().unstack()
coh_size = cust.groupby("acq_month").size()
cohort = pd.DataFrame(np.nan, index=range(12), columns=range(12))
for a in range(12):
    for m in range(a, 12):
        cohort.loc[a, m - a] = coh.loc[a, m] / coh_size[a] if m in coh.columns else np.nan
ch_cac = spend.groupby("channel").spend.sum() / spend.groupby("channel").new_customers.sum()
ch_m3 = {c: np.nanmean([orders[(orders.channel == c) & (orders.acq_month == a) & (orders.month == a + 3)].customer_id.nunique() /
                        (cust[(cust.channel == c) & (cust.acq_month == a)].shape[0]) for a in range(9)]) for c in CH}
c6 = orders[(orders.acq_month.between(0, 5)) & (orders.month - orders.acq_month <= 5)]
ch_rev12 = c6.groupby("channel").order_value.sum() / cust[cust.acq_month <= 5].groupby("channel").size()
# save data
mk.to_csv(os.path.join(OUT, "SYNTHETIC_monthly_kpis.csv"), index=False)
spend.assign(month=[str(MONTHS[m]) for m in spend.month]).to_csv(os.path.join(OUT, "SYNTHETIC_marketing_spend.csv"), index=False)
orders[["order_id", "month_label", "customer_id", "channel", "region", "order_value"]].to_csv(os.path.join(OUT, "SYNTHETIC_orders.csv.gz"), index=False)
cohort.round(4).to_csv(os.path.join(OUT, "SYNTHETIC_cohort_retention.csv"))

def inr(x):
    if x >= 1e7: return f"INR {x/1e7:.2f} Cr"
    if x >= 1e5: return f"INR {x/1e5:.1f} L"
    return f"INR {x:,.0f}"
H1, H2 = mk.iloc[:6], mk.iloc[6:]
tot = dict(revenue=mk.revenue.sum(), orders=mk.orders.sum(), aov=mk.revenue.sum() / mk.orders.sum(),
           cac=mk.spend.sum() / mk.new_customers.sum(), repeat=mk.repeat_rate.iloc[-1], new=mk.new_customers.sum())
def d(a, b): return (b / a - 1) * 100
last, prev = mk.iloc[-1], mk.iloc[-4]  # Q-on-Q style: Sep vs Jun
cmap = LinearSegmentedColormap.from_list("teal", ["#FFFFFF", TEAL_XL, TEAL_L, TEAL, TEAL_D])
CH_COL = [TEAL_D, TEAL, TEAL_L, "#9CC4C6", "#CFE2E3"]

# ---------------- dashboard ----------------
def draw_dashboard(path):
    fig = plt.figure(figsize=(16, 9), dpi=100)
    fig.text(0.02, 0.955, "Northwind Retail", fontsize=24, weight="black", color=INK, va="center")
    fig.text(0.205, 0.955, "D2C Performance Dashboard  ·  Oct 2025 – Sep 2026  ·  Monthly MIS", fontsize=14, color=GREY, va="center")
    sample_badge(fig, y=0.972)
    fig.add_artist(plt.Line2D([0.02, 0.98], [0.915, 0.915], color=RULE, lw=1))
    tiles = [("Revenue (12m)", inr(tot["revenue"]), d(H1.revenue.sum(), H2.revenue.sum()), "H2 vs H1", mk.revenue, True),
             ("Orders (12m)", f"{tot['orders']/1e3:,.1f}k", d(H1.orders.sum(), H2.orders.sum()), "H2 vs H1", mk.orders, True),
             ("Avg order value", inr(tot["aov"]), d(H1.revenue.sum()/H1.orders.sum(), H2.revenue.sum()/H2.orders.sum()), "H2 vs H1", mk.aov, True),
             ("Blended CAC", inr(tot["cac"]), d(H1.spend.sum()/H1.new_customers.sum(), H2.spend.sum()/H2.new_customers.sum()), "H2 vs H1", mk.cac, False),
             ("Repeat rate (Sep)", f"{tot['repeat']*100:.1f}%", (last.repeat_rate - prev.repeat_rate) * 100, "pts vs Jun", mk.repeat_rate, True),
             ("New customers", f"{tot['new']/1e3:,.1f}k", d(H1.new_customers.sum(), H2.new_customers.sum()), "H2 vs H1", mk.new_customers, True)]
    tw, gap, x0, y0, th = 0.152, 0.0112, 0.02, 0.745, 0.145
    for i, (name, val, dl, basis, series, up_good) in enumerate(tiles):
        x = x0 + i * (tw + gap)
        ax = fig.add_axes([x, y0, tw, th]); ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
        for s in ax.spines.values(): s.set_visible(False)
        ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes, fc=TEAL_XXL, ec="none"))
        ax.add_patch(plt.Rectangle((0, 0), 0.018, 1, transform=ax.transAxes, fc=TEAL, ec="none"))
        ax.text(0.08, 0.82, name.upper(), fontsize=9.5, color=GREY, weight="bold", transform=ax.transAxes)
        ax.text(0.08, 0.50, val, fontsize=21, color=INK, weight="black", transform=ax.transAxes)
        good = (dl >= 0) == up_good
        unit = "" if "pts" in basis else "%"
        ax.text(0.08, 0.17, f"{dl:+.1f}{unit}", fontsize=11, weight="bold", color=GREEN if good else RED, transform=ax.transAxes)
        ax.text(0.36, 0.17, basis, fontsize=9.5, color=GREY, transform=ax.transAxes)
        sx = fig.add_axes([x + tw * 0.62, y0 + th * 0.10, tw * 0.33, th * 0.30]); sx.axis("off")
        sx.plot(series.values, color=TEAL, lw=1.6); sx.fill_between(range(12), series.values, series.min() * 0.97, color=TEAL, alpha=0.10)
        sx.set_ylim(series.min() * 0.97, series.max() * 1.02)
    # trend
    ax = fig.add_axes([0.045, 0.415, 0.565, 0.27])
    ax.bar(range(12), mk.revenue / 1e7, color=TEAL_XL, width=0.62, label="Revenue (INR Cr)")
    ax.set_ylabel("Revenue, INR Cr"); ax.set_xticks(range(12)); ax.set_xticklabels(LBL, fontsize=9.5)
    ax.set_title("Revenue & orders trend", pad=8)
    ax2 = ax.twinx(); ax2.plot(range(12), mk.orders / 1e3, color=TEAL, lw=2.5, marker="o", ms=5, label="Orders (k)")
    ax2.set_ylabel("Orders, thousands"); ax2.grid(False); ax2.spines["right"].set_visible(True); ax2.spines["top"].set_visible(False)
    ax2.set_ylim(0, (mk.orders / 1e3).max() * 1.2); ax.set_ylim(0, (mk.revenue / 1e7).max() * 1.2)
    ax.annotate("Festive peak", (1, mk.revenue.iloc[1] / 1e7), xytext=(2.6, mk.revenue.iloc[1] / 1e7 * 1.08), fontsize=9.5, color=GREY,
                arrowprops=dict(arrowstyle="-", color=GREY_L))
    ax.axvline(6.5, color=GREY_L, ls=":", lw=1); ax.text(6.6, (mk.revenue / 1e7).max() * 1.13, "Loyalty programme live (May)", fontsize=9.5, color=GREY)
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left", bbox_to_anchor=(0.30, 1.17), ncol=2, fontsize=9.5)
    # channel mix (100% stacked by quarter)
    ax = fig.add_axes([0.685, 0.415, 0.295, 0.27])
    q = ch_rev.groupby(np.arange(12) // 3).sum(); qs = q.div(q.sum(axis=1), axis=0) * 100
    left = np.zeros(4)
    for c, col in zip(CH, CH_COL):
        ax.barh(range(4), qs[c], left=left, color=col, height=0.62, label=c)
        for j, v in enumerate(qs[c]):
            if v > 7: ax.text(left[j] + v / 2, j, f"{v:.0f}%", ha="center", va="center", fontsize=9, color="white" if col in (TEAL_D, TEAL, TEAL_L) else INK)
        left += qs[c].values
    ax.set_yticks(range(4)); ax.set_yticklabels(["Q3 FY26\n(Oct-Dec)", "Q4 FY26\n(Jan-Mar)", "Q1 FY27\n(Apr-Jun)", "Q2 FY27\n(Jul-Sep)"], fontsize=9)
    ax.invert_yaxis(); ax.set_xlim(0, 100); ax.grid(False); ax.set_xticks([])
    ax.spines["bottom"].set_visible(False); ax.spines["left"].set_visible(False)
    ax.set_title("Revenue mix by acquisition channel", pad=8)
    ax.legend(ncol=5, loc="lower center", bbox_to_anchor=(0.42, -0.2), fontsize=8.3, handlelength=1, columnspacing=0.8)
    # region bar
    ax = fig.add_axes([0.065, 0.105, 0.27, 0.225])
    yy = np.arange(4)
    ax.barh(yy + 0.19, reg_rev_h["H1"] / 1e7, height=0.36, color=TEAL_XL, label="H1 (Oct-Mar)")
    ax.barh(yy - 0.19, reg_rev_h["H2"] / 1e7, height=0.36, color=TEAL, label="H2 (Apr-Sep)")
    for j, r in enumerate(REG):
        g = d(reg_rev_h.loc[r, "H1"], reg_rev_h.loc[r, "H2"])
        ax.text(reg_rev_h.loc[r, "H2"] / 1e7 + 0.05, j - 0.19, f"{g:+.0f}%", va="center", fontsize=9.5, color=TEAL_D, weight="bold")
    ax.set_yticks(yy); ax.set_yticklabels(REG); ax.invert_yaxis(); ax.set_xlabel("Revenue, INR Cr")
    ax.set_xlim(0, reg_rev_h.values.max() / 1e7 * 1.25)
    ax.set_title("Revenue by region, H2 vs H1", pad=8); ax.legend(fontsize=9, loc="lower right")
    # cohort heatmap
    ax = fig.add_axes([0.44, 0.085, 0.50, 0.25])
    M = cohort.values[:, :9] * 100; M[:, 0] = np.nan  # M0 = 100% by definition; show M1..M8
    show = cohort.values[:11, 1:9] * 100
    im = ax.imshow(show, cmap=cmap, aspect="auto", vmin=0, vmax=40)
    for i in range(show.shape[0]):
        for j in range(show.shape[1]):
            v = show[i, j]
            if not np.isnan(v): ax.text(j, i, f"{v:.0f}%", ha="center", va="center", fontsize=8.5, color="white" if v > 24 else INK)
    ax.set_xticks(range(8)); ax.set_xticklabels([f"M{k}" for k in range(1, 9)], fontsize=9)
    ax.set_yticks(range(11)); ax.set_yticklabels(LBL[:11], fontsize=8.5); ax.grid(False)
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_title("Cohort retention: % of acquired customers ordering in month N", pad=8)
    cb = fig.add_axes([0.948, 0.085, 0.008, 0.25]); fig.colorbar(im, cax=cb); cb.tick_params(labelsize=8); cb.set_ylabel("%", fontsize=9)
    footer(fig, "Northwind Retail is a fictional brand; figures are simulated for illustration")
    fig.savefig(path, dpi=100); plt.close(fig)
draw_dashboard(os.path.join(OUT, "northwind_kpi_dashboard.png"))

# ---------------- insight charts for PDF ----------------
def chart_cac():
    fig, ax = plt.subplots(figsize=(7.2, 3.0), dpi=200)
    sp2 = spend.copy(); sp2["cac"] = sp2.spend / sp2.new_customers
    for c, col in zip(CH, CH_COL):
        s = sp2[sp2.channel == c].set_index("month").cac
        ax.plot(range(12), s, color=col if col != "#CFE2E3" else GREY_L, lw=2.4 if c == "Paid Social" else 1.6, label=c)
    ax.set_xticks(range(12)); ax.set_xticklabels(LBL, fontsize=8); ax.set_ylabel("CAC, INR")
    ax.set_title("CAC by channel – paid social is getting expensive", fontsize=11)
    ax.legend(fontsize=8, ncol=5, loc="upper left", bbox_to_anchor=(0, -0.12))
    fig.tight_layout(); p = os.path.join(OUT, "_chart_cac.png"); fig.savefig(p); plt.close(fig); return p
def chart_unit():
    fig, ax = plt.subplots(figsize=(7.2, 2.9), dpi=200)
    ratio = (ch_rev12 / ch_cac).reindex(CH)
    bars = ax.bar(CH, ratio, color=[TEAL if c == "Referral" else TEAL_L for c in CH], width=0.55)
    for b, v, c in zip(bars, ratio, CH):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.3, f"{v:.1f}x", ha="center", fontsize=9, weight="bold", color=TEAL_D)
        ax.text(b.get_x() + b.get_width() / 2, -1.2, f"M3 ret. {ch_m3[c]*100:.0f}%", ha="center", fontsize=8, color=GREY)
    ax.set_ylim(-1.8, ratio.max() * 1.18); ax.axhline(0, color=RULE)
    ax.set_title("6-month revenue per acquired customer ÷ CAC (Oct–Mar cohorts)", fontsize=11); ax.set_ylabel("multiple of CAC")
    fig.tight_layout(); p = os.path.join(OUT, "_chart_unit.png"); fig.savefig(p); plt.close(fig); return p
p_cac, p_unit = chart_cac(), chart_unit()

# ---------------- PDF ----------------
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, KeepTogether
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
rl_setup(); S = rl_styles()
W = A4[0] - 80
doc = SimpleDocTemplate(os.path.join(OUT, "northwind_kpi_mis_report.pdf"), pagesize=A4, leftMargin=40, rightMargin=40,
                        topMargin=46, bottomMargin=54, title="Northwind Retail – KPI & MIS pack (SAMPLE)", author="Shashwat Kumar")
P = lambda t, s="body": Paragraph(t, S[s])
B = lambda t: Paragraph(t, S["bullet"], bulletText="•")
story = []
ps_share = (ch_rev.iloc[-3:]["Paid Social"].sum() / ch_rev.iloc[-3:].sum().sum()) * 100
south_g = d(reg_rev_h.loc["South", "H1"], reg_rev_h.loc["South", "H2"])
rr_h1, rr_h2 = H1.repeat_rate.mean() * 100, H2.repeat_rate.mean() * 100
ps_cac0, ps_cac1 = cac_path["Paid Social"][0], spend[(spend.channel == "Paid Social") & (spend.month == 11)].eval("spend/new_customers").iloc[0]
ref_ratio = (ch_rev12 / ch_cac)["Referral"]; ps_ratio = (ch_rev12 / ch_cac)["Paid Social"]
# Page 1 – exec summary
story += [P("SAMPLE DELIVERABLE · KPI DASHBOARD & MIS", "kicker"), P("Northwind Retail: 12-month performance review"),
          ]
story[-1] = P("Northwind Retail: 12-month performance review", "h1")
story += [P(f"Reporting period Oct 2025 – Sep 2026 · D2C apparel &amp; home (fictional brand) · All numbers simulated", "small"), Spacer(1, 8),
          Image(os.path.join(OUT, "northwind_kpi_dashboard.png"), width=W, height=W * 9 / 16), Spacer(1, 6),
          P("Executive summary", "h2"),
          P(f"Northwind closed the year at <b>{inr(tot['revenue'])}</b> revenue from <b>{tot['orders']/1e3:,.0f}k orders</b> "
            f"(AOV {inr(tot['aov'])}). H2 revenue was {d(H1.revenue.sum(), H2.revenue.sum()):+.1f}% vs H1 despite H1 containing the festive peak, "
            f"so the underlying run-rate is healthy. Growth, however, is being bought at a rising price."),
          B(f"<b>Acquisition cost is the main risk.</b> Paid-social CAC rose from INR {ps_cac0:,.0f} to INR {ps_cac1:,.0f} (+{d(ps_cac0, ps_cac1):.0f}%) while it still drives {ps_share:.0f}% of revenue."),
          B(f"<b>Retention is the main lever.</b> Average repeat rate moved from {rr_h1:.1f}% (H1) to {rr_h2:.1f}% (H2) after the May loyalty launch."),
          B(f"<b>Referral is the most efficient scalable channel</b> at {ref_ratio:.1f}x 6-month revenue-to-CAC vs {ps_ratio:.1f}x for paid social, yet it gets ~5% of spend."),
          B(f"<b>South is the growth region</b> ({south_g:+.0f}% H2 vs H1); East is flat and has the lowest AOV."),
          P("Recommendation in one line: shift 20% of paid-social budget into referral and retention, and set CAC guardrails by channel (page 4).", "callout"),
          PageBreak()]
# Page 2 – KPI dictionary
story += [P("KPI DICTIONARY", "kicker"), P("One definition per number, agreed once", "h1"),
          P("Each KPI below has a single owner, formula, grain and source. This dictionary is the contract between finance, marketing and "
            "the data team; the dashboard and the monthly MIS pack compute every tile from these definitions only."), Spacer(1, 4)]
kd = [["KPI", "Definition & formula", "Grain", "Source", "Owner", "FY27 target"],
      ["Revenue", "Sum of net order value after discounts, excl. GST, returns and cancellations", "Month · channel · region", "OMS orders", "Finance", "INR 68 Cr"],
      ["Orders", "Count of distinct non-cancelled order IDs", "Month · channel · region", "OMS orders", "Ops", "+20% YoY"],
      ["AOV", "Revenue ÷ Orders", "Month · channel", "Derived", "Category", "INR 1,500"],
      ["New customers", "Customers whose first-ever order falls in the month", "Month · acq. channel", "CRM", "Growth", "+15% YoY"],
      ["CAC (blended)", "Total acquisition spend ÷ New customers (paid + content + referral rewards)", "Month · channel", "Ad platforms, finance GL", "Growth", "≤ INR 450"],
      ["CAC (by channel)", "Channel spend ÷ New customers first-touch attributed to that channel", "Month · channel", "Ad platforms + CRM", "Growth", "Channel caps"],
      ["Repeat rate", "Active customers with ≥1 prior order ÷ All active customers in month", "Month", "OMS + CRM", "CRM lead", "≥ 68%"],
      ["Cohort retention (Mn)", "Customers of acquisition month c ordering in month c+n ÷ cohort size", "Cohort × month", "OMS + CRM", "CRM lead", "M3 ≥ 15%"],
      ["Revenue / CAC", "6-month revenue per acquired customer ÷ channel CAC (cohort basis)", "Channel", "Derived", "Growth + Finance", "≥ 3.0x"],
      ["Active customers", "Distinct customers with ≥1 order in month", "Month · region", "OMS", "CRM lead", "Tracked"]]
kd = [[P(x, "cellh") for x in kd[0]]] + [[P(r[0], "cellb")] + [P(x, "cell") for x in r[1:]] for r in kd[1:]]
story += [rl_table(kd, [W * f for f in (0.14, 0.36, 0.14, 0.13, 0.11, 0.12)]), Spacer(1, 10),
          P("Data & refresh rules", "h2"),
          B("Refresh: daily at 06:00 IST for operational tiles; MIS pack frozen on working day 3 of the following month."),
          B("Attribution: first-touch for CAC and cohort channel; last-touch shown separately for campaign optimisation."),
          B("Quality checks: order-to-payment reconciliation (±0.5%), spend-to-GL reconciliation, duplicate customer merge by hashed phone/email."),
          B("Fiscal calendar: April–March (Q1 = Apr–Jun). Festive season flagged Oct–Nov for like-for-like comparisons."),
          P("Note: targets shown are illustrative placeholders for a fictional company.", "small"), PageBreak()]
# Page 3 – insights
story += [P("INSIGHTS", "kicker"), P("What the numbers are saying", "h1"),
          P("1 · Paid social is scaling, but with diminishing returns", "h2"),
          Image(p_cac, width=W, height=W * 3.0 / 7.2),
          P(f"Paid-social CAC climbed steadily (+{d(ps_cac0, ps_cac1):.0f}% over the year) as audiences saturated, while search was broadly stable and "
            f"marketplace and referral were flat. Because paid social is the largest acquisition channel, it is pushing blended CAC up even as volumes grow."),
          P("2 · Unit economics differ sharply by channel", "h2"),
          Image(p_unit, width=W, height=W * 2.9 / 7.2),
          P(f"Referral and organic customers generate more revenue per rupee of acquisition cost and retain better at month 3. Organic cannot be bought directly, so referral (highlighted) is the scalable lever. "
            f"Paid social returns {ps_ratio:.1f}x CAC in its first 6 months, which is thin once gross margin and returns are applied."),
          P("3 · Retention improved after the loyalty launch; South leads growth", "h2"),
          P(f"The cohort heatmap shows month-1 retention lifting for cohorts active after May 2026, and repeat rate rising from {rr_h1:.1f}% to {rr_h2:.1f}%. "
            f"South revenue grew {south_g:+.0f}% H2 vs H1, with higher AOV; East remains the weakest region on both growth and basket size."),
          PageBreak()]
# Page 4 – recommendations
story += [P("RECOMMENDATIONS", "kicker"), P("Five moves for the next two quarters", "h1"), Spacer(1, 4)]
rec = [["#", "Action", "Owner", "Expected impact", "Effort", "When"],
       ["1", "Re-allocate 20% of paid-social budget to referral rewards and retention journeys", "Growth", "Blended CAC −8 to −12%", "Low", "Next 30 days"],
       ["2", "Set channel CAC guardrails (e.g. paid social ≤ INR 650) with weekly alerting", "Growth + Data", "Stops runaway spend early", "Low", "Next 30 days"],
       ["3", "Extend loyalty programme: tiered rewards, second-order nudge at day 21", "CRM", "Repeat rate +3 to +5 pts", "Medium", "Q3 FY27"],
       ["4", "Double down on South: regional creatives, faster delivery SLAs", "Marketing + Ops", "South revenue +15%", "Medium", "Q3 FY27"],
       ["5", "East basket-building: bundles and free-shipping threshold test", "Category", "East AOV +6%", "Low", "Q3 FY27"]]
rec = [[P(x, "cellh") for x in rec[0]]] + [[P(r[0], "cellb"), P(r[1], "cell")] + [P(x, "cell") for x in r[2:]] for r in rec[1:]]
story += [rl_table(rec, [W * f for f in (0.05, 0.42, 0.14, 0.17, 0.09, 0.13)]), Spacer(1, 10),
          P("How we will know it worked", "h2"),
          B("Monthly MIS tracks blended and channel CAC against guardrails, with variance commentary."),
          B("Cohort heatmap reviewed monthly: success = M1 retention ≥ 25% and M3 ≥ 15% for new cohorts."),
          B("Budget shift run as a geo-split test for 6 weeks before full roll-out, so the effect is measured rather than assumed."),
          P("What this sample includes", "h2"),
          B("Live dashboard (Power BI / Looker Studio / Metabase) built on the KPI dictionary above."),
          B("Monthly MIS pack: 6–8 slides with automated commentary and variance flags."),
          B("Data model and SQL / Python transformation scripts, documented and handed over."),
          B("A 60-minute walkthrough and a 30-day support window."),
          Spacer(1, 6),
          P("About this sample: Northwind Retail is a fictional company. All customers, orders, spend and targets were generated synthetically "
            f"({len(cust):,} new customers in-window on a simulated 24-month base, {len(orders):,} orders) by the accompanying Python script, for portfolio illustration only. "
            "Prepared by Shashwat Kumar as an illustrative work sample on synthetic data.", "callout")]
doc.build(story, onFirstPage=rl_page_decor("Northwind Retail · KPI & MIS pack"), onLaterPages=rl_page_decor("Northwind Retail · KPI & MIS pack"))
for p in (p_cac, p_unit): os.remove(p)
print(mk[["month_label", "revenue", "orders", "aov", "cac", "repeat_rate"]].round(2).to_string())
print("customers", len(cust), "orders", len(orders), ch_m3, (ch_rev12 / ch_cac).round(2).to_dict())
