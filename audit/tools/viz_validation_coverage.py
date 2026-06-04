#!/usr/bin/env python3
"""Visualize flywheel validation coverage: which areas of the MAgPIE agent are
thoroughly validated, measured by (a) how often a module/doc has come up across
flywheel rounds and (b) the quality (score) of the answers.

Source of truth: audit/validation_rounds.json (per-round flywheel results; counts read live).
Schema drifted across rounds, so module/score/bug extraction is defensive.

Outputs PNGs into audit/tools/viz_out/.
"""
import json, os, re
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))  # magpie-agent/
OUT = os.path.join(HERE, "viz_out")
os.makedirs(OUT, exist_ok=True)

# ---- module category map (from AGENT.md Quick Module Finder; all 46 modules) ----
CATEGORIES = {
    "Land Use":      [10, 29, 30, 31, 32, 34, 35],
    "Water":         [41, 42, 43],
    "Production":    [14, 17, 18, 20, 70, 71, 73],
    "Carbon/Climate":[52, 53, 56, 57, 58, 59],
    "Nitrogen":      [50, 51, 55],
    "Economics":     [11, 12, 13, 21, 38, 39, 40],
    "Demand":        [9, 15, 16, 60, 62],
    "Environment":   [22, 44, 45, 54],
    "Other":         [28, 36, 37, 80],
}
MOD_NAME = {
    10:"land",29:"cropland",30:"croparea",31:"pasture",32:"forestry",34:"urban",35:"natveg",
    41:"irrig.infra",42:"water dem",43:"water avail",
    14:"yields",17:"production",18:"residues",20:"processing",70:"livestock",71:"lvst disagg",73:"timber",
    52:"carbon",53:"methane",56:"GHG policy",57:"MACC",58:"peatland",59:"SOM",
    50:"soil N",51:"N emis",55:"awms",
    11:"costs",12:"int rate",13:"tech ch",21:"trade",38:"factor cost",39:"landconv",40:"transport",
    9:"drivers",15:"food",16:"demand",60:"bioenergy",62:"material",
    22:"conserv",44:"biodiv",45:"climate",54:"phosphorus",
    28:"age class",36:"employ",37:"labor prod",80:"optim",
}
MOD_TO_CAT = {m:c for c,ms in CATEGORIES.items() for m in ms}
CAT_ORDER = list(CATEGORIES.keys())
CAT_COLOR = dict(zip(CAT_ORDER, plt.cm.tab10(np.linspace(0,1,len(CAT_ORDER)))))

# ---- defensive extractors ----
def get_modules(q):
    """Return set of module ints tested by a question."""
    mods = set()
    for key in ("modules_tested", "modules"):
        v = q.get(key)
        if isinstance(v, list):
            mods.update(int(x) for x in v if isinstance(x,(int,float)))
    # parse module numbers out of docs_tested paths like 'modules/module_28.md'
    dt = q.get("docs_tested")
    if isinstance(dt, list):
        for p in dt:
            m = re.search(r"module_(\d+)", str(p))
            if m: mods.add(int(m.group(1)))
    return mods

def get_nonmodule_docs(q):
    """Non-module docs touched (cross_module/reference/core_docs paths)."""
    out = []
    dt = q.get("docs_tested")
    if isinstance(dt, list):
        for p in dt:
            p = str(p)
            if "module_" in p:  # module doc, handled elsewhere
                continue
            out.append(p)
    return out

def get_score(q):
    s = q.get("score")
    if isinstance(s,(int,float)): return float(s)
    for k in ("score_for_mean","original_score"):
        v=q.get(k)
        if isinstance(v,(int,float)): return float(v)
    return None

def get_bugs(q):
    for k in ("bugs_total","bugs_found","bugs"):
        v=q.get(k)
        if isinstance(v,(int,float)): return float(v)
    # else sum severities
    tot=0; any_=False
    for k in ("bugs_critical","bugs_major","bugs_minor","bugs_significant","bugs_informational","bugs_nitpick"):
        v=q.get(k)
        if isinstance(v,(int,float)): tot+=v; any_=True
    return float(tot) if any_ else None

# ---- aggregate ----
data = json.load(open(os.path.join(ROOT,"audit","validation_rounds.json")))
rounds = data["rounds"]

mod = defaultdict(lambda: {"n":0,"scores":[],"bugs":0.0,"rounds":[],"score_rounds":[]})  # per module
round_summary = []  # (round, mean_score, total_bugs)
nonmod = defaultdict(lambda: {"n":0,"scores":[],"bugs":0.0})

MAXR = max(r.get("round") for r in rounds if isinstance(r.get("round"),(int,float)))
DECAY = 0.92  # per-round recency decay for recency-weighted frequency

for rd in rounds:
    rnum = rd.get("round")
    qscores=[]; qbugs=0.0
    for q in rd.get("questions",[]):
        sc = get_score(q); bg = get_bugs(q)
        if sc is not None: qscores.append(sc)
        if bg is not None: qbugs += bg
        mods = get_modules(q)
        for m in mods:
            mod[m]["n"]+=1
            if sc is not None:
                mod[m]["scores"].append(sc)
                if isinstance(rnum,(int,float)):
                    mod[m]["score_rounds"].append((rnum, sc))  # (round, score) pairs, in order
            if bg is not None: mod[m]["bugs"] += bg/max(len(mods),1)  # share bugs across modules
            mod[m]["rounds"].append(rnum)
        for p in get_nonmodule_docs(q):
            nonmod[p]["n"]+=1
            if sc is not None: nonmod[p]["scores"].append(sc)
            if bg is not None: nonmod[p]["bugs"]+=bg
    # round-level summary from explicit summary if present, else from questions
    summ = rd.get("summary",{})
    ms = summ.get("mean_score")
    if not isinstance(ms,(int,float)):
        ms = float(np.mean(qscores)) if qscores else None
    tb = summ.get("total_bugs")
    if not isinstance(tb,(int,float)):
        tb = qbugs
    if isinstance(rnum,(int,float)) and ms is not None:
        round_summary.append((rnum, ms, tb))

# all 46 modules, fill zeros for untested
all_mods = sorted(MOD_TO_CAT.keys())
def mstats(m):
    d=mod.get(m)
    if not d or d["n"]==0:
        return dict(n=0, mean=None, latest=None, latest_round=None, rwfreq=0.0, bugs=0.0)
    sr=d["score_rounds"]
    latest = sr[-1][1] if sr else None
    latest_round = sr[-1][0] if sr else None
    # recency-weighted frequency: each scored test weighted DECAY^(MAXR-round)
    rwfreq = sum(DECAY**(MAXR-rnd) for rnd,_ in sr)
    return dict(n=d["n"], mean=float(np.mean(d["scores"])) if d["scores"] else None,
                latest=latest, latest_round=latest_round, rwfreq=rwfreq, bugs=d["bugs"])
STAT = {m:mstats(m) for m in all_mods}

# ================= FIGURE 1: module coverage map (category-grouped heatmap) =====
def fig_coverage_map():
    fig, ax = plt.subplots(figsize=(13, 8.5))
    cmap = plt.cm.RdYlGn
    norm = plt.Normalize(4, 10)  # scores roughly 4..10
    y = 0
    yticks=[]; ylabels=[]
    maxcols = max(len(v) for v in CATEGORIES.values())
    for cat in CAT_ORDER:
        mods = CATEGORIES[cat]
        yticks.append(y+0.5); ylabels.append(cat)
        for i,m in enumerate(mods):
            s=STAT[m]
            if s["n"]==0:
                color="#d9d9d9"; txtcol="#555555"
            else:
                color=cmap(norm(s["mean"]));
                # luminance for text contrast
                r,g,b,_=color
                txtcol="white" if (0.299*r+0.587*g+0.114*b)<0.55 else "black"
            ax.add_patch(Rectangle((i,y),0.96,0.96,facecolor=color,edgecolor="white",lw=1.5))
            label=f"{m:02d} {MOD_NAME.get(m,'')}"
            sub = "untested" if s["n"]==0 else f"n={s['n']}  {s['mean']:.1f}"
            ax.text(i+0.48, y+0.62, label, ha="center", va="center", fontsize=7.0, color=txtcol, weight="bold")
            ax.text(i+0.48, y+0.30, sub, ha="center", va="center", fontsize=6.5, color=txtcol)
        y+=1
    ax.set_xlim(0,maxcols); ax.set_ylim(0,y)
    ax.invert_yaxis()
    ax.set_yticks(yticks); ax.set_yticklabels(ylabels, fontsize=10, weight="bold")
    ax.set_xticks([])
    for spine in ax.spines.values(): spine.set_visible(False)
    sm=plt.cm.ScalarMappable(cmap=cmap,norm=norm); sm.set_array([])
    cb=fig.colorbar(sm, ax=ax, fraction=0.025, pad=0.01)
    cb.set_label("Mean flywheel score (answer quality)", fontsize=9)
    ax.set_title("MAgPIE agent: module validation coverage map\n"
                 f"cell = module, color = mean answer-quality score, n = times tested across {len(rounds)} flywheel rounds; grey = never tested",
                 fontsize=12, weight="bold")
    fig.tight_layout()
    p=os.path.join(OUT,"1_module_coverage_map.png"); fig.savefig(p,dpi=150,bbox_inches="tight"); plt.close(fig)
    return p

# ================= FIGURE 2: thoroughness scatter =================
def fig_thoroughness_scatter():
    fig, ax = plt.subplots(figsize=(12,8))
    for m in all_mods:
        s=STAT[m]
        if s["n"]==0: continue
        cat=MOD_TO_CAT[m]
        size = 60 + s["bugs"]*35
        ax.scatter(s["n"], s["mean"], s=size, color=CAT_COLOR[cat],
                   edgecolor="black", lw=0.6, alpha=0.82, zorder=3)
        ax.annotate(f"{m:02d}", (s["n"], s["mean"]), fontsize=7.5,
                    ha="center", va="center", zorder=4, weight="bold")
    # untested modules listed in a corner note
    untested=[m for m in all_mods if STAT[m]["n"]==0]
    # median guide lines
    ns=[STAT[m]["n"] for m in all_mods if STAT[m]["n"]>0]
    scs=[STAT[m]["mean"] for m in all_mods if STAT[m]["n"]>0]
    medn=np.median(ns); meds=np.median(scs)
    ax.axvline(medn, color="grey", ls="--", lw=1, alpha=0.7)
    ax.axhline(meds, color="grey", ls="--", lw=1, alpha=0.7)
    ax.text(0.99,0.01,f"median n={medn:.0f}, median score={meds:.1f}",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=8, color="grey")
    # quadrant labels
    xmax=max(ns)+0.6
    ax.text(xmax*0.97, 9.8, "thoroughly validated\n& solid", ha="right", fontsize=9, color="green", alpha=0.7, weight="bold")
    ax.text(medn*0.5, 9.8, "looks good but\nlightly tested", ha="center", fontsize=9, color="darkorange", alpha=0.8, weight="bold")
    ax.text(xmax*0.97, scs and min(scs) or 5, "heavily scrutinized,\nstill weak", ha="right", va="bottom", fontsize=9, color="firebrick", alpha=0.8, weight="bold")
    ax.set_xlabel("Times tested across flywheel rounds  (validation frequency)", fontsize=11)
    ax.set_ylabel("Mean answer-quality score", fontsize=11)
    ax.set_title("Validation thoroughness by module\nbubble size ∝ bugs found (shared across co-tested modules); label = module number",
                 fontsize=12, weight="bold")
    # legend for categories
    from matplotlib.lines import Line2D
    handles=[Line2D([0],[0],marker="o",color="w",markerfacecolor=CAT_COLOR[c],markeredgecolor="k",markersize=9,label=c) for c in CAT_ORDER]
    leg1=ax.legend(handles=handles, title="Category", fontsize=8, title_fontsize=9, loc="lower left", framealpha=0.9)
    ax.add_artist(leg1)
    if untested:
        ax.text(0.01,0.99,"Never tested: "+", ".join(f"{m:02d}" for m in untested),
                transform=ax.transAxes, va="top", ha="left", fontsize=8, color="firebrick",
                bbox=dict(boxstyle="round", fc="#fff0f0", ec="firebrick", alpha=0.9))
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    p=os.path.join(OUT,"2_thoroughness_scatter.png"); fig.savefig(p,dpi=150,bbox_inches="tight"); plt.close(fig)
    return p

# ================= FIGURE 3: flywheel score trend over rounds =================
def fig_score_trend():
    rs=sorted(round_summary, key=lambda x:x[0])
    rn=[x[0] for x in rs]; ms=[x[1] for x in rs]; tb=[x[2] for x in rs]
    fig, ax1=plt.subplots(figsize=(13,6))
    # break the line where rounds are non-consecutive (R31-R40 were doc-centric,
    # no classic mean score) so we don't interpolate across a real gap
    rn_arr=np.array(rn,dtype=float); ms_arr=np.array(ms,dtype=float)
    seg=ms_arr.copy()
    gaps=np.where(np.diff(rn_arr)>1)[0]
    ms_broken=ms_arr.astype(float).copy()
    ms_plot=ms_broken.tolist()
    # insert NaN breaks
    rn_b=[]; ms_b=[]
    for i in range(len(rn)):
        rn_b.append(rn[i]); ms_b.append(ms[i])
        if i in gaps:
            rn_b.append(rn[i]+0.01); ms_b.append(np.nan)
    ax1.plot(rn_b,ms_b,"-o",color="#2166ac",lw=2,markersize=5,label="Mean score (classic Q-rounds)",zorder=3)
    if len(gaps):
        ax1.axvspan(rn[gaps[0]]+0.5, rn[gaps[0]+1]-0.5, color="grey", alpha=0.10, zorder=0)
        ax1.text((rn[gaps[0]]+rn[gaps[0]+1])/2, 5.25, "R31–R40\ndoc-centric\n(no classic score)",
                 ha="center", va="bottom", fontsize=8, color="grey", style="italic")
    # rolling mean (consecutive segment only, up to first gap)
    cut = gaps[0]+1 if len(gaps) else len(ms)
    if cut>=3:
        k=3; rmean=np.convolve(ms[:cut],np.ones(k)/k,mode="valid")
        ax1.plot(rn[k-1:cut],rmean,"--",color="#2166ac",alpha=0.5,lw=1.5,label=f"{k}-round rolling mean")
    ax1.set_xlabel("Flywheel round",fontsize=11)
    ax1.set_ylabel("Mean answer-quality score",color="#2166ac",fontsize=11)
    ax1.tick_params(axis="y",labelcolor="#2166ac")
    ax1.set_ylim(5,10.2)
    ax1.grid(True,alpha=0.25)
    ax2=ax1.twinx()
    ax2.bar(rn,tb,color="#d6604d",alpha=0.3,width=0.7,label="Bugs found",zorder=1)
    ax2.set_ylabel("Bugs found per round",color="#b2182b",fontsize=11)
    ax2.tick_params(axis="y",labelcolor="#b2182b")
    ax1.set_zorder(ax2.get_zorder()+1); ax1.patch.set_visible(False)
    ax1.set_title("Flywheel maturation: answer quality rises and bug yield falls across rounds\n"
                  "(later rounds shift to doc-centric / regression-anchor probing)",fontsize=12,weight="bold")
    l1,la1=ax1.get_legend_handles_labels(); l2,la2=ax2.get_legend_handles_labels()
    ax1.legend(l1+l2,la1+la2,loc="lower right",fontsize=9,framealpha=0.9)
    fig.tight_layout()
    p=os.path.join(OUT,"3_score_trend.png"); fig.savefig(p,dpi=150,bbox_inches="tight"); plt.close(fig)
    return p

# ================= FIGURE 4: per-category aggregate =================
def fig_category_aggregate():
    cats=CAT_ORDER
    coverage=[]; meanscore=[]; ntests=[]; ntested_mods=[]
    for c in cats:
        mods=CATEGORIES[c]
        tested=[m for m in mods if STAT[m]["n"]>0]
        ntested_mods.append((len(tested),len(mods)))
        coverage.append(len(tested)/len(mods)*100)
        ntests.append(sum(STAT[m]["n"] for m in mods))
        allsc=[STAT[m]["mean"] for m in tested if STAT[m]["mean"] is not None]
        meanscore.append(np.mean(allsc) if allsc else np.nan)
    fig,(axA,axB)=plt.subplots(1,2,figsize=(15,6))
    yp=np.arange(len(cats))
    # left: coverage % with tested/total annotation, colored by mean score
    cmap=plt.cm.RdYlGn; norm=plt.Normalize(6,9.5)
    barcols=[cmap(norm(s)) if not np.isnan(s) else "#cccccc" for s in meanscore]
    axA.barh(yp, coverage, color=barcols, edgecolor="black", lw=0.5)
    for i,(t,tot) in enumerate(ntested_mods):
        axA.text(coverage[i]+1.5, i, f"{t}/{tot} modules", va="center", fontsize=8.5)
    axA.set_yticks(yp); axA.set_yticklabels(cats, fontsize=10)
    axA.invert_yaxis(); axA.set_xlim(0,118)
    axA.set_xlabel("% of modules in category tested at least once", fontsize=10)
    axA.set_title("Coverage breadth (bar fill color = mean score)", fontsize=11, weight="bold")
    sm=plt.cm.ScalarMappable(cmap=cmap,norm=norm); sm.set_array([])
    cb=fig.colorbar(sm,ax=axA,fraction=0.04,pad=0.02); cb.set_label("mean score",fontsize=8)
    # right: total tests (validation effort) per category
    order=np.argsort(ntests)
    axB.barh(np.arange(len(cats)),[ntests[i] for i in order],
             color=[CAT_COLOR[cats[i]] for i in order],edgecolor="black",lw=0.5)
    axB.set_yticks(np.arange(len(cats))); axB.set_yticklabels([cats[i] for i in order],fontsize=10)
    for j,i in enumerate(order):
        axB.text(ntests[i]+0.5,j,str(ntests[i]),va="center",fontsize=9,weight="bold")
    axB.set_xlabel("Total module-tests (validation effort/depth)",fontsize=10)
    axB.set_title("Validation effort by category",fontsize=11,weight="bold")
    axB.set_xlim(0,max(ntests)*1.15)
    fig.suptitle("Validation coverage & quality aggregated by functional category",fontsize=13,weight="bold")
    fig.tight_layout()
    p=os.path.join(OUT,"4_category_aggregate.png"); fig.savefig(p,dpi=150,bbox_inches="tight"); plt.close(fig)
    return p

# ================= FIGURE 5: CURRENT-quality coverage map (latest score) =====
STALE_BEFORE = MAXR - 5  # latest test older than this => flag as stale "current" score
def fig_current_quality_map():
    fig, ax = plt.subplots(figsize=(13, 8.5))
    cmap = plt.cm.RdYlGn; norm = plt.Normalize(4, 10)
    y=0; yticks=[]; ylabels=[]
    maxcols=max(len(v) for v in CATEGORIES.values())
    for cat in CAT_ORDER:
        yticks.append(y+0.5); ylabels.append(cat)
        for i,m in enumerate(CATEGORIES[cat]):
            s=STAT[m]
            stale = s["latest_round"] is not None and s["latest_round"]<STALE_BEFORE
            if s["latest"] is None:
                color="#d9d9d9"; txtcol="#555"
            else:
                color=cmap(norm(s["latest"])); r,g,b,_=color
                txtcol="white" if (0.299*r+0.587*g+0.114*b)<0.55 else "black"
            ax.add_patch(Rectangle((i,y),0.96,0.96,facecolor=color,
                         edgecolor=("#b2182b" if stale else "white"),
                         lw=(2.5 if stale else 1.5),
                         hatch=("////" if stale else None)))
            label=f"{m:02d} {MOD_NAME.get(m,'')}"
            sub = "untested" if s["latest"] is None else f"R{int(s['latest_round'])}  {s['latest']:.1f}"
            ax.text(i+0.48,y+0.62,label,ha="center",va="center",fontsize=7.0,color=txtcol,weight="bold")
            ax.text(i+0.48,y+0.30,sub,ha="center",va="center",fontsize=6.5,color=txtcol)
        y+=1
    ax.set_xlim(0,maxcols); ax.set_ylim(0,y); ax.invert_yaxis()
    ax.set_yticks(yticks); ax.set_yticklabels(ylabels,fontsize=10,weight="bold"); ax.set_xticks([])
    for sp in ax.spines.values(): sp.set_visible(False)
    sm=plt.cm.ScalarMappable(cmap=cmap,norm=norm); sm.set_array([])
    cb=fig.colorbar(sm,ax=ax,fraction=0.025,pad=0.01); cb.set_label("Latest answer-quality score",fontsize=9)
    ax.set_title("MAgPIE agent: CURRENT validation quality (most-recent score per module)\n"
                 f"cell color = score at the latest round that tested it; 'R## x.x' = that round + score; "
                 f"red hatched = last tested before R{STALE_BEFORE} (score may be outdated)",
                 fontsize=11.5, weight="bold")
    fig.tight_layout()
    p=os.path.join(OUT,"5_current_quality_map.png"); fig.savefig(p,dpi=150,bbox_inches="tight"); plt.close(fig)
    return p

# ================= FIGURE 6: trajectory mean -> latest (improvement) =========
def fig_trajectory():
    rows=[m for m in all_mods if STAT[m]["mean"] is not None and STAT[m]["latest"] is not None]
    rows.sort(key=lambda m: STAT[m]["latest"])
    fig,ax=plt.subplots(figsize=(10,12))
    yp=np.arange(len(rows))
    for j,m in enumerate(rows):
        s=STAT[m]; a=s["mean"]; b=s["latest"]
        imp = b-a
        col = "#1a9850" if imp>0.05 else ("#d73027" if imp<-0.05 else "grey")
        ax.plot([a,b],[j,j],color=col,lw=2,alpha=0.6,zorder=1)
        ax.scatter(a,j,color="#bbbbbb",edgecolor="black",lw=0.5,s=45,zorder=2)  # all-rounds mean
        ax.scatter(b,j,color=col,edgecolor="black",lw=0.5,s=70,zorder=3)        # latest
        stale = s["latest_round"] is not None and s["latest_round"]<STALE_BEFORE
        ax.annotate(f"R{int(s['latest_round'])}",(b,j),xytext=(4,0),textcoords="offset points",
                    va="center",fontsize=6.5,color=("#b2182b" if stale else "#444"))
    ax.set_yticks(yp); ax.set_yticklabels([f"{m:02d} {MOD_NAME.get(m,'')}" for m in rows],fontsize=8)
    ax.set_xlabel("Answer-quality score",fontsize=11)
    ax.set_xlim(5.5,10.3)
    ax.grid(True,axis="x",alpha=0.25)
    from matplotlib.lines import Line2D
    leg=[Line2D([0],[0],marker="o",color="w",markerfacecolor="#bbbbbb",markeredgecolor="k",markersize=8,label="all-rounds mean"),
         Line2D([0],[0],marker="o",color="w",markerfacecolor="#1a9850",markeredgecolor="k",markersize=9,label="latest score (improved)"),
         Line2D([0],[0],marker="o",color="w",markerfacecolor="#d73027",markeredgecolor="k",markersize=9,label="latest score (regressed)")]
    ax.legend(handles=leg,fontsize=8.5,loc="lower right",framealpha=0.95)
    ax.set_title("Trajectory: all-rounds mean -> latest score, per module\n"
                 "right-shift (green) = docs improved since early probing; R## = round of latest test (red = stale)",
                 fontsize=12,weight="bold")
    fig.tight_layout()
    p=os.path.join(OUT,"6_trajectory.png"); fig.savefig(p,dpi=150,bbox_inches="tight"); plt.close(fig)
    return p

# ================= FIGURE 7: recency-weighted thoroughness scatter ===========
def fig_recency_scatter():
    fig,ax=plt.subplots(figsize=(12,8))
    for m in all_mods:
        s=STAT[m]
        if s["rwfreq"]<=0 or s["latest"] is None: continue
        cat=MOD_TO_CAT[m]
        ax.scatter(s["rwfreq"],s["latest"],s=60+s["bugs"]*35,color=CAT_COLOR[cat],
                   edgecolor="black",lw=0.6,alpha=0.82,zorder=3)
        ax.annotate(f"{m:02d}",(s["rwfreq"],s["latest"]),fontsize=7.5,ha="center",va="center",zorder=4,weight="bold")
    xs=[STAT[m]["rwfreq"] for m in all_mods if STAT[m]["rwfreq"]>0]
    ys=[STAT[m]["latest"] for m in all_mods if STAT[m]["latest"] is not None and STAT[m]["rwfreq"]>0]
    medx=np.median(xs); medy=np.median(ys)
    ax.axvline(medx,color="grey",ls="--",lw=1,alpha=0.7); ax.axhline(medy,color="grey",ls="--",lw=1,alpha=0.7)
    ax.text(0.99,0.01,f"median recency-wt freq={medx:.1f}, median latest={medy:.1f}",
            transform=ax.transAxes,ha="right",va="bottom",fontsize=8,color="grey")
    ax.text(0.99,0.97,"validated recently,\noften & well",transform=ax.transAxes,ha="right",va="top",
            fontsize=9,color="green",alpha=0.75,weight="bold")
    ax.set_xlabel(f"Recency-weighted test frequency  (each test weighted {DECAY}^(R{int(MAXR)}-round))",fontsize=11)
    ax.set_ylabel("Latest answer-quality score",fontsize=11)
    ax.set_title("Current thoroughness: recency-weighted frequency vs latest score\n"
                 "x rewards recent+repeated testing; bubble size ∝ bugs found",fontsize=12,weight="bold")
    from matplotlib.lines import Line2D
    handles=[Line2D([0],[0],marker="o",color="w",markerfacecolor=CAT_COLOR[c],markeredgecolor="k",markersize=9,label=c) for c in CAT_ORDER]
    ax.legend(handles=handles,title="Category",fontsize=8,title_fontsize=9,loc="lower left",framealpha=0.9)
    ax.grid(True,alpha=0.25)
    fig.tight_layout()
    p=os.path.join(OUT,"7_recency_weighted_scatter.png"); fig.savefig(p,dpi=150,bbox_inches="tight"); plt.close(fig)
    return p

# ============ FIGURE 8: dual-axis global health timeline (semantic + structural) ====
def fig_global_timeline():
    from datetime import datetime
    DATE_FLOOR = datetime(2026,2,1)  # project start; defensive guard against any pre-project typo'd round date
    def pdate(s):
        try:
            dt = datetime.strptime(str(s)[:10], "%Y-%m-%d")
            return dt if dt >= DATE_FLOOR else None
        except Exception: return None
    # semantic: (date, mean_score, total_bugs) per round that has a date + mean
    sem=[]
    for rd in rounds:
        dt=pdate(rd.get("date"));
        if dt is None: continue
        summ=rd.get("summary",{})
        ms=summ.get("mean_score")
        if not isinstance(ms,(int,float)):
            qs=[get_score(q) for q in rd.get("questions",[]) if get_score(q) is not None]
            ms=float(np.mean(qs)) if qs else None
        tb=summ.get("total_bugs")
        if not isinstance(tb,(int,float)):
            tb=sum(get_bugs(q) or 0 for q in rd.get("questions",[]))
        if ms is not None: sem.append((dt,ms,tb))
    sem.sort(key=lambda x:x[0])
    # structural: pipeline audits
    pa=json.load(open(os.path.join(ROOT,"audit","pipeline_audit_rounds.json")))["rounds"]
    SEV=["CRITICAL","HIGH","MEDIUM","LOW"]
    SEVCOL={"CRITICAL":"#67000d","HIGH":"#d6604d","MEDIUM":"#f4a582","LOW":"#fddbc7"}
    struct=[]
    for r in pa:
        dt=pdate(r.get("date")); bs=r.get("by_severity") or {}
        if dt is None or not bs: continue
        struct.append((dt,{s:bs.get(s,0) for s in SEV},r.get("findings_total")))
    struct.sort(key=lambda x:x[0])

    fig,(axT,axB)=plt.subplots(2,1,figsize=(13,9),sharex=True,
                               gridspec_kw={"height_ratios":[1,1],"hspace":0.12})
    # --- top: semantic answer quality ---
    sd=[x[0] for x in sem]; sm=[x[1] for x in sem]; sb=[x[2] for x in sem]
    axTb=axT.twinx()
    axTb.bar(sd,sb,width=4,color="#d6604d",alpha=0.25,label="bugs found / round")
    axT.plot(sd,sm,"-o",color="#2166ac",lw=2,markersize=4,label="mean answer-quality score",zorder=5)
    axT.set_ylabel("Mean answer score",color="#2166ac",fontsize=10); axT.set_ylim(5,10.3)
    axT.tick_params(axis="y",labelcolor="#2166ac")
    axTb.set_ylabel("Bugs / round",color="#b2182b",fontsize=9); axTb.tick_params(axis="y",labelcolor="#b2182b")
    axT.set_zorder(axTb.get_zorder()+1); axT.patch.set_visible(False)
    axT.set_title(f"AXIS 1 — Semantic answer quality (validation_rounds.json, {len(rounds)} rounds)",fontsize=10.5,weight="bold",loc="left")
    axT.grid(True,alpha=0.2)
    # --- bottom: structural machinery health ---
    pd_=[x[0] for x in struct]
    bottoms=np.zeros(len(struct))
    for s in SEV:
        vals=np.array([x[1][s] for x in struct],dtype=float)
        axB.bar(pd_,vals,bottom=bottoms,width=4,color=SEVCOL[s],edgecolor="white",lw=0.4,label=s.title())
        bottoms+=vals
    for x in struct:
        axB.text(x[0],sum(x[1].values())+1.5,str(int(sum(x[1].values()))),ha="center",fontsize=7.5,color="#444")
    axB.set_ylabel("Pipeline-audit findings",fontsize=10)
    axB.set_title(f"AXIS 2 — Structural / machinery health (pipeline_audit_rounds.json, {len(pa)} rounds; stacked by severity)",fontsize=10.5,weight="bold",loc="left")
    axB.grid(True,axis="y",alpha=0.2)
    axB.legend(fontsize=8,ncol=4,loc="upper right",framealpha=0.9,title="severity")
    axT.legend(fontsize=8,loc="lower right",framealpha=0.9)
    fig.suptitle("Global agent-quality timeline: answer accuracy AND machinery health\n"
                 "both axes improving; structural audits begin late-May, findings fall 82→15 with criticals eliminated",
                 fontsize=12.5,weight="bold")
    fig.autofmt_xdate()
    fig.tight_layout(rect=[0,0,1,0.96])
    p=os.path.join(OUT,"8_global_health_timeline.png"); fig.savefig(p,dpi=150,bbox_inches="tight"); plt.close(fig)
    return p

paths=[fig_coverage_map(), fig_thoroughness_scatter(), fig_score_trend(), fig_category_aggregate(),
       fig_current_quality_map(), fig_trajectory(), fig_recency_scatter(), fig_global_timeline()]

# ---- text summary for the user ----
print("=== DATASET ===")
print(f"rounds={len(rounds)}  questions={sum(len(r.get('questions',[])) for r in rounds)}")
tested=[m for m in all_mods if STAT[m]['n']>0]
print(f"modules tested at least once: {len(tested)}/46")
print(f"never tested: {[m for m in all_mods if STAT[m]['n']==0]}")
print()
print("Most-tested modules (n, mean score, ~bugs):")
for m in sorted(all_mods,key=lambda m:-STAT[m]['n'])[:10]:
    s=STAT[m]
    print(f"  M{m:02d} {MOD_NAME.get(m,''):12s} n={s['n']:2d}  mean={s['mean']:.1f}  bugs~{s['bugs']:.0f}")
print()
print("Lowest mean score among tested (potential weak spots, n>=2):")
weak=[m for m in tested if STAT[m]['n']>=2]
for m in sorted(weak,key=lambda m:STAT[m]['mean'])[:8]:
    s=STAT[m]
    print(f"  M{m:02d} {MOD_NAME.get(m,''):12s} n={s['n']:2d}  mean={s['mean']:.1f}")
print()
print("=== CURRENT QUALITY (latest score per module) ===")
print(f"stale threshold: last tested before R{STALE_BEFORE}")
stale=[m for m in tested if STAT[m]['latest_round'] is not None and STAT[m]['latest_round']<STALE_BEFORE]
print("stale current-scores (%d): " % len(stale)+", ".join("M%02d(R%d)"%(m,STAT[m]['latest_round']) for m in stale))
print()
print("Lowest LATEST score (current weak spots):")
for m in sorted(tested,key=lambda m:STAT[m]['latest'])[:8]:
    s=STAT[m]
    print("  M%02d %-12s latest=%.1f (R%d)  mean=%.1f" % (m,MOD_NAME.get(m,''),s['latest'],s['latest_round'],s['mean']))
print()
print("Biggest improvers (latest - mean):")
imp=sorted(tested,key=lambda m:-(STAT[m]['latest']-STAT[m]['mean']))
for m in imp[:6]:
    s=STAT[m]; print("  M%02d %-12s %.1f -> %.1f  (+%.1f)" % (m,MOD_NAME.get(m,''),s['mean'],s['latest'],s['latest']-s['mean']))
print("Biggest regressors (latest < mean):")
for m in imp[::-1][:6]:
    s=STAT[m]; d=s['latest']-s['mean']
    if d<0: print("  M%02d %-12s %.1f -> %.1f  (%.1f)" % (m,MOD_NAME.get(m,''),s['mean'],s['latest'],d))
print()
for p in paths: print("WROTE", p)
