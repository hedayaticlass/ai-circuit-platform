"""
Evaluator
=========

نتایج benchmark را تحلیل و جداول آماده برای مقاله تولید می‌کند.

نحوه اجرا:
    python benchmark/evaluator.py --input benchmark/results/results_TIMESTAMP.json
    python benchmark/evaluator.py --input benchmark/results/results_TIMESTAMP.json --latex
"""

import argparse
import json
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def load_results(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def compute_by_category(results: list) -> dict:
    cats = defaultdict(lambda: {"total": 0, "cir": 0, "topo": 0, "spice": 0, "sim": 0})
    for r in results:
        cat = r["category"]
        p   = r["pipeline"]
        cats[cat]["total"] += 1
        if p.get("cir_generated"):   cats[cat]["cir"]   += 1
        if p.get("cir_valid"):       cats[cat]["topo"]  += 1
        if p.get("spice_generated"): cats[cat]["spice"] += 1
        if p.get("sim_success"):     cats[cat]["sim"]   += 1
    return dict(cats)


def compute_by_difficulty(results: list) -> dict:
    diffs = defaultdict(lambda: {"total": 0, "cir": 0, "topo": 0, "sim": 0})
    for r in results:
        d = r["difficulty"]
        p = r["pipeline"]
        diffs[d]["total"] += 1
        if p.get("cir_generated"): diffs[d]["cir"]  += 1
        if p.get("cir_valid"):     diffs[d]["topo"] += 1
        if p.get("sim_success"):   diffs[d]["sim"]  += 1
    return dict(diffs)


def pct(num, den):
    return round(num / den * 100, 1) if den > 0 else 0.0


def print_summary_table(data: dict, by_category: dict, by_difficulty: dict,
                        baseline: dict | None = None):
    m = data["summary"]["metrics"]
    n = data["summary"]["total_circuits"]

    print("\n" + "="*65)
    print("  TABLE I — Overall Pipeline Performance")
    print("="*65)
    print(f"  {'Metric':<35} {'Value':>8}  {'Count':>10}")
    print("-"*65)
    print(f"  {'CIR Generation Rate':<35} {m['cir_generation_rate']:>7.1f}%  {int(n*m['cir_generation_rate']/100):>5}/{n}")
    print(f"  {'Topological Validity Rate':<35} {m['topological_validity']:>7.1f}%  {int(n*m['topological_validity']/100):>5}/{n}")
    print(f"  {'SPICE Generation Rate':<35} {m['spice_generation_rate']:>7.1f}%  {int(n*m['spice_generation_rate']/100):>5}/{n}")
    print(f"  {'Simulation Success Rate':<35} {m['simulation_success']:>7.1f}%  {int(n*m['simulation_success']/100):>5}/{n}")
    print(f"  {'Average Latency (ms)':<35} {m['avg_latency_ms']:>8.0f}")

    if baseline:
        print("\n  --- Baseline (Direct LLM→SPICE) ---")
        print(f"  {'SPICE Validity Rate':<35} {baseline.get('spice_validity_rate',0):>7.1f}%")
        print(f"  {'Simulation Success Rate':<35} {baseline.get('simulation_success',0):>7.1f}%")
        delta = m["simulation_success"] - baseline.get("simulation_success", 0)
        print(f"\n  Improvement (CIR pipeline vs baseline): +{delta:.1f} pp")

    print("\n" + "="*65)
    print("  TABLE II — Results by Category")
    print("="*65)
    print(f"  {'Category':<20} {'N':>4}  {'CIR%':>6}  {'Topo%':>6}  {'Sim%':>6}")
    print("-"*65)
    for cat, v in sorted(by_category.items()):
        t = v["total"]
        print(f"  {cat:<20} {t:>4}  {pct(v['cir'],t):>6.1f}  {pct(v['topo'],t):>6.1f}  {pct(v['sim'],t):>6.1f}")

    print("\n" + "="*65)
    print("  TABLE III — Results by Difficulty")
    print("="*65)
    print(f"  {'Difficulty':<15} {'N':>4}  {'CIR%':>6}  {'Topo%':>6}  {'Sim%':>6}")
    print("-"*65)
    for diff in ["easy", "medium", "hard"]:
        if diff in by_difficulty:
            v = by_difficulty[diff]
            t = v["total"]
            print(f"  {diff:<15} {t:>4}  {pct(v['cir'],t):>6.1f}  {pct(v['topo'],t):>6.1f}  {pct(v['sim'],t):>6.1f}")


def print_latex_tables(data: dict, by_category: dict, by_difficulty: dict,
                       baseline: dict | None = None):
    """جداول LaTeX آماده برای کپی در مقاله."""
    m  = data["summary"]["metrics"]
    n  = data["summary"]["total_circuits"]
    md = data["summary"].get("model", "GPT")

    print("\n% ======= TABLE I — Overall =======")
    print(r"\begin{table}[h]")
    print(r"\centering")
    print(r"\caption{Overall Pipeline Performance (" + md + r")}")
    print(r"\label{tab:overall}")
    print(r"\begin{tabular}{lrr}")
    print(r"\hline")
    print(r"\textbf{Metric} & \textbf{Rate (\%)} & \textbf{Count} \\")
    print(r"\hline")
    print(f"CIR Generation       & {m['cir_generation_rate']:.1f} & {int(n*m['cir_generation_rate']/100)}/{n} \\\\")
    print(f"Topological Validity & {m['topological_validity']:.1f} & {int(n*m['topological_validity']/100)}/{n} \\\\")
    print(f"SPICE Generation     & {m['spice_generation_rate']:.1f} & {int(n*m['spice_generation_rate']/100)}/{n} \\\\")
    print(f"Simulation Success   & {m['simulation_success']:.1f} & {int(n*m['simulation_success']/100)}/{n} \\\\")
    if baseline:
        print(r"\hline")
        print(f"\\textit{{Baseline Sim.}} & \\textit{{{baseline.get('simulation_success',0):.1f}}} & — \\\\")
    print(r"\hline")
    print(f"Avg. Latency (ms)   & \\multicolumn{{2}}{{r}}{{{m['avg_latency_ms']:.0f}}} \\\\")
    print(r"\hline")
    print(r"\end{tabular}")
    print(r"\end{table}")

    print("\n% ======= TABLE II — By Category =======")
    print(r"\begin{table}[h]")
    print(r"\centering")
    print(r"\caption{Pipeline Performance by Circuit Category}")
    print(r"\label{tab:category}")
    print(r"\begin{tabular}{lrrrr}")
    print(r"\hline")
    print(r"\textbf{Category} & \textbf{N} & \textbf{CIR\%} & \textbf{Topo\%} & \textbf{Sim\%} \\")
    print(r"\hline")
    for cat, v in sorted(by_category.items()):
        t = v["total"]
        print(f"{cat.replace('_',' ').title()} & {t} & {pct(v['cir'],t):.1f} & {pct(v['topo'],t):.1f} & {pct(v['sim'],t):.1f} \\\\")
    print(r"\hline")
    print(r"\end{tabular}")
    print(r"\end{table}")

    print("\n% ======= TABLE III — By Difficulty =======")
    print(r"\begin{table}[h]")
    print(r"\centering")
    print(r"\caption{Pipeline Performance by Difficulty Level}")
    print(r"\label{tab:difficulty}")
    print(r"\begin{tabular}{lrrrr}")
    print(r"\hline")
    print(r"\textbf{Difficulty} & \textbf{N} & \textbf{CIR\%} & \textbf{Topo\%} & \textbf{Sim\%} \\")
    print(r"\hline")
    for diff in ["easy", "medium", "hard"]:
        if diff in by_difficulty:
            v = by_difficulty[diff]
            t = v["total"]
            print(f"{diff.capitalize()} & {t} & {pct(v['cir'],t):.1f} & {pct(v['topo'],t):.1f} & {pct(v['sim'],t):.1f} \\\\")
    print(r"\hline")
    print(r"\end{tabular}")
    print(r"\end{table}")


def print_failure_analysis(results: list):
    """تحلیل دقیق خطاها — برای بخش Discussion مقاله."""
    failures = [r for r in results if not r["pipeline"].get("sim_success")]
    if not failures:
        print("\n✅ همه مدارها موفق بودند!")
        return

    print(f"\n{'='*65}")
    print(f"  تحلیل خطاها ({len(failures)} مدار)")
    print(f"{'='*65}")

    no_cir     = [r for r in failures if not r["pipeline"].get("cir_generated")]
    bad_topo   = [r for r in failures if r["pipeline"].get("cir_generated") and not r["pipeline"].get("cir_valid")]
    no_spice   = [r for r in failures if r["pipeline"].get("cir_valid") and not r["pipeline"].get("spice_generated")]
    no_sim     = [r for r in failures if r["pipeline"].get("spice_generated") and not r["pipeline"].get("sim_success")]

    if no_cir:
        print(f"\n  ❌ CIR تولید نشد ({len(no_cir)}):")
        for r in no_cir[:3]:
            print(f"     [{r['id']}] {r['pipeline'].get('error','')[:70]}")

    if bad_topo:
        print(f"\n  ⚠️  مشکل توپولوژی ({len(bad_topo)}):")
        for r in bad_topo[:3]:
            warnings = r["pipeline"].get("topo_warnings", [])
            print(f"     [{r['id']}] {warnings[0][:70] if warnings else 'unknown'}")

    if no_spice:
        print(f"\n  ⚠️  SPICE تولید نشد ({len(no_spice)}):")
        for r in no_spice[:3]:
            print(f"     [{r['id']}] {r['pipeline'].get('error','')[:70]}")

    if no_sim:
        print(f"\n  ⚠️  شبیه‌سازی ناموفق ({len(no_sim)}):")
        for r in no_sim[:3]:
            print(f"     [{r['id']}] {r['pipeline'].get('sim_error','')[:70]}")


def main():
    parser = argparse.ArgumentParser(description="Benchmark Evaluator")
    parser.add_argument("--input",   required=True, help="مسیر فایل نتایج JSON")
    parser.add_argument("--latex",   action="store_true", help="خروجی LaTeX برای مقاله")
    parser.add_argument("--failures",action="store_true", help="تحلیل خطاها")
    args = parser.parse_args()

    path = ROOT / args.input if not Path(args.input).is_absolute() else Path(args.input)
    if not path.exists():
        print(f"❌ فایل یافت نشد: {path}")
        sys.exit(1)

    data = load_results(path)
    results   = data["results"]
    by_cat    = compute_by_category(results)
    by_diff   = compute_by_difficulty(results)
    baseline  = data["summary"].get("baseline_metrics")

    print(f"\n📊 تحلیل نتایج: {path.name}")
    print(f"   مدل: {data['summary'].get('model','unknown')}")
    print(f"   تاریخ: {data['summary'].get('timestamp','')[:19]}")

    if args.latex:
        print_latex_tables(data, by_cat, by_diff, baseline)
    else:
        print_summary_table(data, by_cat, by_diff, baseline)

    if args.failures:
        print_failure_analysis(results)


if __name__ == "__main__":
    main()
