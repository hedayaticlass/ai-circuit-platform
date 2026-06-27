"""
نقطه ورود اصلی API (FastAPI).

اجرا با:
    uvicorn api.main:app --reload

این فایل فقط orchestration است: درخواست‌ها را به ماژول‌های
core/services تحویل می‌دهد و خطاها را به پاسخ HTTP مناسب تبدیل می‌کند.
منطق اصلی همیشه باید در core/ یا services/ باشد، نه اینجا.
"""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from core.cir import Circuit
from services.cir_to_spice.basic_converter import BasicCIRToSpice, CIRToSpiceError
from services.cir_to_spice.spice_parser import BasicSpiceToCIR, SpiceParseError
from services.schematic.schemdraw_generator import (
    SchemdrawSchematicGenerator,
    SchematicGenerationError,
)
from services.spice_analyzer.pyspice_analyzer import PySpiceAnalyzer, SpiceAnalysisError
from services.spice_analyzer.transient_analyzer import (
    PySpiceTransientAnalyzer,
    TransientAnalysisError,
)
from services.text_to_cir.openai_text_to_cir import OpenAITextToCIR, TextToCIRError
from services.text_to_cir.llm_circuit_improver import LLMCircuitImprover, CircuitImproverError

app = FastAPI(
    title="AI Circuit Platform API",
    description="پلتفرم متن‌باز طراحی، تحلیل و آموزش مدارهای الکتریکی/الکترونیکی با هوش مصنوعی",
    version="0.1.0",
)

# CORS برای توسعه محلی با فرانت‌اند React (vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # در production محدود شود
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class TextToCIRRequest(BaseModel):
    description: str


class NetlistRequest(BaseModel):
    netlist: str


class SchematicRequest(BaseModel):
    circuit: Circuit


class ImproveRequest(BaseModel):
    circuit: Circuit
    goal: str
    analysis_results: dict | None = None


class SimulateRequest(BaseModel):
    circuit: Circuit
    step_time: float = 1e-5    # گام زمانی (ثانیه)
    end_time: float  = 1e-3    # زمان پایان (ثانیه)
    start_time: float = 0.0    # زمان شروع ذخیره
    max_step: float | None = None
    # حداکثر نقاط بازگشتی — برای جلوگیری از payload خیلی بزرگ
    max_points: int = 2000


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/text-to-cir", response_model=Circuit)
def text_to_cir(payload: TextToCIRRequest) -> Circuit:
    """توضیح متنی مدار -> CIR (با استفاده از AI)."""
    converter = OpenAITextToCIR()
    try:
        return converter.convert(payload.description)
    except TextToCIRError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/cir-to-spice")
def cir_to_spice(circuit: Circuit) -> dict:
    """CIR -> نت‌لیست SPICE (دترمینیستیک، بدون AI)."""
    converter = BasicCIRToSpice()
    try:
        netlist = converter.convert(circuit)
    except CIRToSpiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"spice": netlist}


@app.post("/api/spice-to-cir", response_model=Circuit)
def spice_to_cir(payload: NetlistRequest) -> Circuit:
    """نت‌لیست SPICE -> CIR (دترمینیستیک)."""
    parser = BasicSpiceToCIR()
    try:
        return parser.parse(payload.netlist)
    except SpiceParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/cir-to-schematic")
def cir_to_schematic(payload: SchematicRequest):
    """CIR -> تصویر شماتیک (PNG)."""
    generator = SchemdrawSchematicGenerator()
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            output_path = Path(tmp.name)
        generator.render(payload.circuit, output_path)
    except SchematicGenerationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return FileResponse(output_path, media_type="image/png", filename="schematic.png")


@app.post("/api/analyze")
def analyze_circuit(circuit: Circuit) -> dict:
    """تحلیل DC operating point یک مدار با PySpice/ngspice.

    قبل از ارسال به ngspice، مدار از نظر مشکلات توپولوژیک معمول (گره
    بلاتکلیف، منبع ولتاژ موازی با مسیر مقاومت-صفر) بررسی می‌شود تا به‌جای
    خطای مبهم ngspice، پیام واضح فارسی نمایش داده شود.
    """
    issues = circuit.validate_circuit()
    if issues:
        raise HTTPException(
            status_code=400,
            detail="مدار مشکل توپولوژیک دارد و قابل تحلیل نیست:\n- " + "\n- ".join(issues),
        )

    spice_converter = BasicCIRToSpice()
    analyzer = PySpiceAnalyzer()

    try:
        netlist = spice_converter.convert(circuit)
    except CIRToSpiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        results = analyzer.analyze(circuit, netlist)
    except SpiceAnalysisError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"spice": netlist, "results": results}


@app.post("/api/simulate")
def simulate_circuit(payload: SimulateRequest) -> dict:
    """شبیه‌سازی transient مدار با PySpice/ngspice.

    خروجی: آرایه‌های زمان + ولتاژ هر گره + جریان هر شاخه در طول زمان.
    برای جلوگیری از payload بزرگ، اگر نقاط بیش از max_points بود،
    داده‌ها به‌صورت یکنواخت نازک‌سازی (downsample) می‌شوند.
    """
    issues = payload.circuit.validate_circuit()
    if issues:
        raise HTTPException(
            status_code=400,
            detail="مدار مشکل توپولوژیک دارد:\n- " + "\n- ".join(issues),
        )

    spice_converter = BasicCIRToSpice()
    try:
        netlist = spice_converter.convert(payload.circuit)
    except CIRToSpiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    from core.interfaces.transient_analyzer import TransientParams
    params = TransientParams(
        step_time=payload.step_time,
        end_time=payload.end_time,
        start_time=payload.start_time,
        max_step=payload.max_step,
    )

    analyzer = PySpiceTransientAnalyzer()
    try:
        result = analyzer.simulate(netlist, params)
    except TransientAnalysisError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # downsample اگر نقاط خیلی زیاد بود
    n = len(result.time)
    step = max(1, n // payload.max_points)
    indices = list(range(0, n, step))

    def sample(arr: list[float]) -> list[float]:
        return [arr[i] for i in indices]

    return {
        "time": sample(result.time),
        "node_voltages": {k: sample(v) for k, v in result.node_voltages.items()},
        "branch_currents": {k: sample(v) for k, v in result.branch_currents.items()},
        "metadata": result.metadata,
        "netlist": netlist,
    }


@app.post("/api/improve")
def improve_circuit(payload: ImproveRequest) -> dict:
    """بهبود مدار بر اساس دستور کاربر (با AI).

    ورودی: CIR فعلی + دستور متنی (مثلاً «ولتاژ گره ۲ را بیشتر کن»)
          + نتایج تحلیل قبلی (اختیاری، برای راهنمایی بهتر AI)
    خروجی: CIR اصلاح‌شده + توضیح فارسی تغییرات
    """
    improver = LLMCircuitImprover()
    try:
        new_circuit, explanation = improver.improve(
            payload.circuit, payload.goal, payload.analysis_results
        )
    except CircuitImproverError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "circuit": new_circuit.model_dump(),
        "explanation": explanation,
        "warnings": new_circuit.metadata.get("validation_warnings", []),
    }


@app.post("/api/text-to-spice")
def text_to_spice(payload: TextToCIRRequest) -> dict:
    """مسیر ترکیبی راحت: متن -> CIR -> SPICE (برای سازگاری با UI فعلی)."""
    text_converter = OpenAITextToCIR()
    spice_converter = BasicCIRToSpice()

    try:
        circuit = text_converter.convert(payload.description)
    except TextToCIRError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        netlist = spice_converter.convert(circuit)
    except CIRToSpiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "circuit": circuit.model_dump(),
        "spice": netlist,
        "warnings": circuit.metadata.get("validation_warnings", []),
    }
