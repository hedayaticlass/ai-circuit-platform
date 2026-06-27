/**
 * کلاینت ساده برای ارتباط با backend (FastAPI).
 *
 * آدرس backend از متغیر محیطی VITE_API_BASE_URL خوانده می‌شود (فایل .env در
 * ریشه frontend). اگر تنظیم نشده باشد، آدرس پیش‌فرض محیط توسعه استفاده می‌شود.
 */

const DEFAULT_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function postJSON(path, body) {
  let response;
  try {
    response = await fetch(`${DEFAULT_BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiError(
      `عدم دسترسی به سرور (${DEFAULT_BASE_URL}). آیا backend اجرا شده است؟`,
      0
    );
  }

  let data = null;
  try {
    data = await response.json();
  } catch {
    // بدنه پاسخ JSON نبود؛ data همان null می‌ماند
  }

  if (!response.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map((d) => d.msg ?? JSON.stringify(d)).join('، ')
      : detail || response.statusText || 'خطای ناشناخته از سرور';
    throw new ApiError(message, response.status);
  }

  return data;
}

/**
 * توضیح متنی مدار -> CIR (با استفاده از AI)
 * @param {string} description
 * @returns {Promise<object>} CIR
 */
export function textToCIR(description) {
  return postJSON('/api/text-to-cir', { description });
}

/**
 * CIR -> نت‌لیست SPICE (دترمینیستیک)
 * @param {object} circuit CIR
 * @returns {Promise<{spice: string}>}
 */
export function cirToSpice(circuit) {
  return postJSON('/api/cir-to-spice', circuit);
}

/**
 * تحلیل DC operating point یک مدار (نیاز به ngspice روی backend دارد)
 * @param {object} circuit CIR
 * @returns {Promise<{spice: string, results: {node_voltages: object, branch_currents: object}}>}
 */
export function analyzeCircuit(circuit) {
  return postJSON('/api/analyze', circuit);
}

/**
 * شبیه‌سازی transient مدار
 * @param {object} circuit CIR
 * @param {{stepTime, endTime, startTime, maxPoints}} params پارامترهای شبیه‌سازی
 * @returns {Promise<{time, node_voltages, branch_currents, metadata, netlist}>}
 */
export function simulateCircuit(circuit, params = {}) {
  return postJSON('/api/simulate', {
    circuit,
    step_time:   params.stepTime   ?? 1e-5,
    end_time:    params.endTime    ?? 1e-3,
    start_time:  params.startTime  ?? 0,
    max_points:  params.maxPoints  ?? 2000,
  });
}

/**
 * بهبود مدار با AI بر اساس دستور کاربر
 * @param {object} circuit CIR فعلی
 * @param {string} goal دستور کاربر به زبان طبیعی
 * @param {object|null} analysisResults نتایج تحلیل قبلی (اختیاری)
 * @returns {Promise<{circuit: object, explanation: string, warnings: string[]}>}
 */
export function improveCircuit(circuit, goal, analysisResults = null) {
  return postJSON('/api/improve', { circuit, goal, analysis_results: analysisResults });
}
