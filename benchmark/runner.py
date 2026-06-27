"""
Benchmark Runner
================

اجرای کامل pipeline روی تمام مدارهای dataset و ذخیره نتایج برای مقاله.

نحوه اجرا:
    cd D:\\Projects\\ai-circuit-platform
    .venv\\Scripts\\activate
    python benchmark/runner.py

    # یا با گزینه‌ها:
    python benchmark/runner.py --model gpt-4o-mini --limit 10 --output results.json
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# اضافه کردن root پروژه به PYTHONPATH
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from core.llm.client import LLMClient
from services.text_to_cir.openai_text_to_cir import OpenAITextToCIR
from services.cir_to_spice.basic_converter import BasicCIRToSpice


def run_pipeline(description: str, client: LLMClient) -> dict:
    """یک توصیف متنی را از طریق کل pipeline اجرا می‌کند و نتایج را برمی‌گرداند."""
    result = {
        "cir_generated":       False,
        "cir_valid":           False,
        "topo_warnings":       [],
        "spice_generated":     False,
        "spice_text":          None,
        "sim_attempted":       False,
        "sim_success":         False,
        "sim_error":           None,
        "component_count":     0,
        "node_count":          0,
        "latency_ms":          0,
        "error":               None,
    }

    t0 = time.time()

    # --- مرحله ۱: Text → CIR ---
    try:
        converter = OpenAITextToCIR(client=client)
        circuit = converter.convert(description)
        result["cir_generated"] = True
        result["component_count"] = len(circuit.components)
        result["node_count"] = len(circuit.get_node_names())
        result["topo_warnings"] = circuit.validate_circuit()
        result["cir_valid"] = len(result["topo_warnings"]) == 0
    except Exception as e:
        result["error"] = f"CIR generation failed: {e}"
        result["latency_ms"] = int((time.time() - t0) * 1000)
        return result

    # --- مرحله ۲: CIR → SPICE ---
    try:
        spice_conv = BasicCIRToSpice()
        netlist = spice_conv.convert(circuit)
        result["spice_generated"] = True
        result["spice_text"] = netlist
    except Exception as e:
        result["error"] = f"SPICE conversion failed: {e}"
        result["latency_ms"] = int((time.time() - t0) * 1000)
        return result

    # --- مرحله ۳: SPICE Simulation (DC .op) ---
    try:
        from PySpice.Spice.Parser import SpiceParser
        result["sim_attempted"] = True
        parser = SpiceParser(source=netlist)
        sim_circuit = parser.build_circuit()
        simulator = sim_circuit.simulator(temperature=25, nominal_temperature=25)
        _ = simulator.operating_point()
        result["sim_success"] = True
    except ImportError:
        result["sim_error"] = "PySpice not installed"
    except Exception as e:
        result["sim_error"] = str(e)[:200]

    result["latency_ms"] = int((time.time() - t0) * 1000)
    return result


def run_baseline(description: str, client: LLMClient) -> dict:
    """
    Baseline: مستقیماً از LLM بخواهید SPICE نت‌لیست تولید کند — بدون CIR واسط.
    این روش رقیب اصلی در مقاله است.
    """
    result = {
        "spice_generated": False,
        "spice_valid":     False,
        "sim_success":     False,
        "sim_error":       None,
        "latency_ms":      0,
        "error":           None,
    }

    baseline_prompt = """You are a SPICE netlist generator.
Convert the circuit description to a valid SPICE netlist.
Return ONLY the raw netlist text, nothing else.
Follow SPICE3/ngspice syntax exactly.
Always include .end at the end."""

    t0 = time.time()

    try:
        raw = client.chat(baseline_prompt, description)
        # پاک‌سازی کد fence
        netlist = raw.strip()
        for fence in ["```spice", "```netlist", "```", "~~~"]:
            netlist = netlist.replace(fence, "")
        netlist = netlist.strip()

        result["spice_generated"] = True
        result["spice_valid"] = ".end" in netlist.lower()

        # تست شبیه‌سازی
        try:
            from PySpice.Spice.Parser import SpiceParser
            parser = SpiceParser(source=netlist)
            sim_circuit = parser.build_circuit()
            simulator = sim_circuit.simulator(temperature=25, nominal_temperature=25)
            _ = simulator.operating_point()
            result["sim_success"] = True
        except Exception as e:
            result["sim_error"] = str(e)[:200]

    except Exception as e:
        result["error"] = str(e)[:200]

    result["latency_ms"] = int((time.time() - t0) * 1000)
    return result


def main():
    parser = argparse.ArgumentParser(description="AI Circuit Platform Benchmark Runner")
    parser.add_argument("--dataset",    default="benchmark/dataset/circuits.json",
                        help="مسیر فایل dataset (پیش‌فرض: benchmark/dataset/circuits.json)")
    parser.add_argument("--output",     default=None,
                        help="مسیر فایل خروجی JSON (پیش‌فرض: benchmark/results/TIMESTAMP.json)")
    parser.add_argument("--limit",      type=int, default=None,
                        help="محدود کردن تعداد مدارها برای تست سریع")
    parser.add_argument("--baseline",   action="store_true",
                        help="اجرای baseline (مستقیم LLM→SPICE) به همراه pipeline اصلی")
    parser.add_argument("--category",   default=None,
                        help="فقط یک دسته خاص را اجرا کن (مثلاً: dc_basic, bjt, filter)")
    parser.add_argument("--no-sim",     action="store_true",
                        help="شبیه‌سازی ngspice را رد کن (اگر ngspice نصب نیست)")
    args = parser.parse_args()

    # بارگذاری dataset
    dataset_path = ROOT / args.dataset
    if not dataset_path.exists():
        print(f"❌ فایل dataset یافت نشد: {dataset_path}")
        sys.exit(1)

    with open(dataset_path, encoding="utf-8") as f:
        circuits = json.load(f)

    # فیلتر دسته
    if args.category:
        circuits = [c for c in circuits if c["category"] == args.category]
        print(f"📂 دسته انتخاب‌شده: {args.category} ({len(circuits)} مدار)")

    # محدودیت تعداد
    if args.limit:
        circuits = circuits[:args.limit]

    print(f"\n{'='*60}")
    print(f"  AI Circuit Platform — Benchmark Runner")
    print(f"{'='*60}")
    print(f"  مدارها: {len(circuits)}")
    print(f"  مدل: {os.environ.get('LLM_MODEL', 'not set')}")
    print(f"  baseline: {'بله' if args.baseline else 'خیر'}")
    print(f"  شبیه‌سازی: {'خیر (--no-sim)' if args.no_sim else 'بله'}")
    print(f"{'='*60}\n")

    # ساخت کلاینت LLM
    try:
        client = LLMClient()
    except Exception as e:
        print(f"❌ خطا در اتصال به LLM: {e}")
        print("   مطمئن شوید LLM_API_KEY در فایل .env تنظیم شده است.")
        sys.exit(1)

    results = []
    ok_cir = ok_topo = ok_spice = ok_sim = 0
    baseline_ok_spice = baseline_ok_sim = 0
    total_latency = 0

    for i, circuit_def in enumerate(circuits):
        cid = circuit_def["id"]
        desc = circuit_def["description"]
        cat  = circuit_def["category"]
        diff = circuit_def["difficulty"]

        print(f"[{i+1:02d}/{len(circuits)}] {cid} ({cat}/{diff})")
        print(f"         {desc[:70]}{'...' if len(desc)>70 else ''}")

        entry = {
            "id":          cid,
            "category":    cat,
            "difficulty":  diff,
            "description": desc,
            "expected_components":  circuit_def.get("expected_components", []),
            "expected_node_count":  circuit_def.get("expected_node_count", 0),
        }

        # --- Pipeline اصلی ---
        r = run_pipeline(desc, client)

        if args.no_sim:
            r["sim_attempted"] = False

        entry["pipeline"] = r

        # آمار
        if r["cir_generated"]:   ok_cir   += 1
        if r["cir_valid"]:       ok_topo  += 1
        if r["spice_generated"]: ok_spice += 1
        if r["sim_success"]:     ok_sim   += 1
        total_latency += r["latency_ms"]

        # خلاصه نتیجه
        status = "✅" if r["cir_valid"] else ("⚠️" if r["cir_generated"] else "❌")
        sim_status = "✅ sim" if r["sim_success"] else ("⚠️" if r["sim_attempted"] else "—")
        print(f"         {status} CIR | {sim_status} | {r['latency_ms']}ms")

        if r["topo_warnings"]:
            for w in r["topo_warnings"][:2]:
                print(f"         ⚠️  {w[:80]}")

        if r["error"] and not r["cir_generated"]:
            print(f"         ❌ {r['error'][:80]}")

        # --- Baseline (اختیاری) ---
        if args.baseline:
            b = run_baseline(desc, client)
            entry["baseline"] = b
            if b["spice_valid"]:  baseline_ok_spice += 1
            if b["sim_success"]:  baseline_ok_sim   += 1
            bst = "✅" if b["sim_success"] else ("⚠️" if b["spice_valid"] else "❌")
            print(f"         Baseline: {bst} | {b['latency_ms']}ms")

        results.append(entry)
        print()

    # ذخیره نتایج
    output_dir = ROOT / "benchmark" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.output:
        output_path = ROOT / args.output
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"results_{ts}.json"

    n = len(circuits)
    summary = {
        "timestamp":           datetime.now().isoformat(),
        "model":               os.environ.get("LLM_MODEL", "unknown"),
        "total_circuits":      n,
        "metrics": {
            "cir_generation_rate":    round(ok_cir   / n * 100, 1),
            "topological_validity":   round(ok_topo  / n * 100, 1),
            "spice_generation_rate":  round(ok_spice / n * 100, 1),
            "simulation_success":     round(ok_sim   / n * 100, 1),
            "avg_latency_ms":         round(total_latency / n),
        },
    }

    if args.baseline:
        summary["baseline_metrics"] = {
            "spice_validity_rate":  round(baseline_ok_spice / n * 100, 1),
            "simulation_success":   round(baseline_ok_sim   / n * 100, 1),
        }

    output_data = {"summary": summary, "results": results}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    # گزارش نهایی
    print(f"\n{'='*60}")
    print(f"  نتایج نهایی")
    print(f"{'='*60}")
    m = summary["metrics"]
    print(f"  CIR Generation Rate:    {m['cir_generation_rate']:6.1f}%  ({ok_cir}/{n})")
    print(f"  Topological Validity:   {m['topological_validity']:6.1f}%  ({ok_topo}/{n})")
    print(f"  SPICE Generation Rate:  {m['spice_generation_rate']:6.1f}%  ({ok_spice}/{n})")
    print(f"  Simulation Success:     {m['simulation_success']:6.1f}%  ({ok_sim}/{n})")
    print(f"  Avg Latency:            {m['avg_latency_ms']:6.0f} ms")

    if args.baseline:
        bm = summary["baseline_metrics"]
        print(f"\n  --- Baseline (مستقیم LLM→SPICE) ---")
        print(f"  SPICE Validity Rate:    {bm['spice_validity_rate']:6.1f}%")
        print(f"  Simulation Success:     {bm['simulation_success']:6.1f}%")
        print(f"\n  بهبود simulation:  +{m['simulation_success']-bm['simulation_success']:.1f}pp")

    print(f"\n  نتایج ذخیره شد: {output_path}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
