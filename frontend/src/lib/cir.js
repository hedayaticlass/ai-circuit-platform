/**
 * Adapter بین مدل داخلی ویرایشگر شماتیک (CircuitBuilder) و CIR
 * (Circuit Intermediate Representation که در core/cir/schema.py تعریف شده).
 *
 * مدل UI:
 *   هر component: { id, type ('R'|'C'|'L'|'D'|'V'|'Joint'), prefix, name,
 *                    value, node1, node2, x, y, rotation }
 *   - `id`   شناسه داخلی React (برای key/drag/select) — معادل مفهومی ندارد در CIR
 *   - `name` نام نمایشی/SPICE (مثل R1, C2) — معادل `Component.id` در CIR
 *   - هر wire فقط برای رسم خط بین دو پایه استفاده می‌شود؛ توپولوژی الکتریکی
 *     واقعی همیشه در node1/node2 هر component نگه داشته می‌شود.
 *
 * CIR:
 *   { components: [{ id, type, value, nodes, label, properties }], metadata }
 *
 * محدودیت فعلی (نسخه ۱ این adapter):
 *   فقط المان‌های دوپایه که UI برایشان سمبل دارد پشتیبانی می‌شوند:
 *   resistor, capacitor, inductor, diode, voltage_source.
 *   سایر انواع CIR (ترانزیستور، opamp، IC، ...) در cirToUiModel نادیده گرفته
 *   می‌شوند و در warnings گزارش می‌شوند — افزودن سمبل/پشتیبانی برای آن‌ها
 *   کار آینده است (نیازی به تغییر این adapter ندارد، فقط نگاشت اضافه می‌شود).
 */

export const UI_TO_CIR_TYPE = {
  R:    'resistor',
  C:    'capacitor',
  L:    'inductor',
  D:    'diode',
  V:    'voltage_source',
  VAC:  'ac_voltage_source',
  // ولتمتر: در SPICE به صورت مقاومت بسیار بزرگ (1 گیگاهم) شبیه‌سازی می‌شود
  // تا جریان نگیرد اما ولتاژ بین دو گره خوانده شود.
  VM:   'resistor',
  // آمپرمتر: در SPICE به صورت منبع ولتاژ صفر ولت سری شبیه‌سازی می‌شود
  // (روش استاندارد SPICE برای خواندن جریان)
  AM:   'voltage_source',
  NPN:  'bjt_npn',
  PNP:  'bjt_pnp',
  NMOS: 'mosfet_n',
  PMOS: 'mosfet_p',
  JFET: 'jfet',
  OPAMP:'opamp',
};

// پیشوند SPICE برای هر نوع UI (برای نام‌گذاری خودکار)
export const UI_TYPE_PREFIX = {
  R: 'R', C: 'C', L: 'L', D: 'D', V: 'V',
  NPN: 'Q', PNP: 'Q', NMOS: 'M', PMOS: 'M',
};

const THREE_PIN_UI_TYPES = new Set(['NPN', 'PNP', 'NMOS', 'PMOS']);

export const CIR_TO_UI_TYPE = Object.fromEntries(
  Object.entries(UI_TO_CIR_TYPE).map(([ui, cir]) => [cir, ui])
);

const GROUND_NODE = '0';

let _uidCounter = 0;
function uid(prefix = 'c') {
  _uidCounter += 1;
  return `${prefix}_${Date.now()}_${_uidCounter}`;
}

/**
 * چیدمان لایه‌ای ساده برای مدارهایی که موقعیت ندارند (مثلاً تولیدشده توسط AI).
 *
 * ایده: مدار را به‌صورت یک گراف می‌بینیم که گره‌های الکتریکی (node) راس‌ها
 * هستند و هر المان یک یال بین دو گره. با BFS از گره زمین ("0")، هر گره یک
 * «عمق» (depth) می‌گیرد. سپس هر المان در ستونی متناظر با عمق گره‌ی نزدیک‌تر
 * به زمین قرار می‌گیرد، و داخل آن ستون به‌صورت عمودی چیده می‌شود.
 *
 * این روش باعث می‌شود:
 *  - المان‌های سری (که گره‌های متوالی دارند) از چپ به راست قرار بگیرند.
 *  - المان‌های موازی (که دو سر مشترک دارند) به‌جای روی‌هم‌افتادن، در یک
 *    ستون اما با فاصله عمودی از هم چیده شوند.
 *
 * این یک الگوریتم layout کامل/general-purpose نیست (مثل force-directed یا
 * Sugiyama)؛ برای مدارهای ساده و متوسط (سری/موازی/ترکیبی) که در این فاز از
 * پروژه هدف هستیم کافی است. برای مدارهای بسیار پیچیده (حلقه‌های متعدد)،
 * بهبود این الگوریتم کار آینده است.
 */
function computeLayeredLayout(components) {
  const COL_WIDTH = 140;
  const ROW_HEIGHT = 90;
  const START_X = 100;
  const START_Y = 100;

  // ساخت لیست مجاورت گره‌ها بر اساس المان‌ها
  const adjacency = new Map(); // node -> Set(neighborNode)
  const addEdge = (a, b) => {
    if (!adjacency.has(a)) adjacency.set(a, new Set());
    if (!adjacency.has(b)) adjacency.set(b, new Set());
    adjacency.get(a).add(b);
    adjacency.get(b).add(a);
  };
  components.forEach((c) => {
    const ns = c.nodes;
    for (let i = 0; i < ns.length; i++)
      for (let j = i + 1; j < ns.length; j++)
        addEdge(ns[i], ns[j]);
  });

  // BFS از گره زمین برای محاسبه عمق هر گره
  const depth = new Map();
  const startNode = adjacency.has('0') ? '0' : components[0]?.nodes[0];
  if (startNode !== undefined) {
    depth.set(startNode, 0);
    const queue = [startNode];
    while (queue.length > 0) {
      const current = queue.shift();
      const currentDepth = depth.get(current);
      for (const neighbor of adjacency.get(current) ?? []) {
        if (!depth.has(neighbor)) {
          depth.set(neighbor, currentDepth + 1);
          queue.push(neighbor);
        }
      }
    }
  }
  // گره‌های جداافتاده (در گراف اصلی نیستند) را به انتها می‌چسبانیم
  let maxDepthSoFar = Math.max(0, ...depth.values());
  for (const node of adjacency.keys()) {
    if (!depth.has(node)) {
      maxDepthSoFar += 1;
      depth.set(node, maxDepthSoFar);
    }
  }

  // هر المان در ستونِ min(depth گره‌هایش) قرار می‌گیرد
  const columnOf = (comp) => Math.min(...comp.nodes.map(n => depth.get(n) ?? 0));

  const rowCounters = new Map(); // column -> تعداد المان‌های قرارگرفته در آن ستون
  const positions = new Map(); // comp.id -> {x, y}

  // مرتب‌سازی پایدار بر اساس ستون تا المان‌های هم‌ستون کنار هم چیده شوند
  const sorted = [...components].sort((a, b) => columnOf(a) - columnOf(b));

  for (const comp of sorted) {
    const col = columnOf(comp);
    const row = rowCounters.get(col) ?? 0;
    rowCounters.set(col, row + 1);

    positions.set(comp.id, {
      x: START_X + col * COL_WIDTH,
      y: START_Y + row * ROW_HEIGHT,
    });
  }

  return positions;
}

/**
 * مدل UI -> CIR
 *
 * @param {Array} components آرایه‌ی components از state ویرایشگر
 * @param {{title?: string}} [options]
 * @returns {object} یک CIR معتبر (مطابق Circuit در core/cir/schema.py)
 */
export function uiModelToCIR(components, options = {}) {
  const cirComponents = [];

  for (const comp of components) {
    if (comp.type === 'Joint') continue; // Joint فقط برای routing بصری است، المان الکتریکی نیست

    const cirType = UI_TO_CIR_TYPE[comp.type];
    if (!cirType) continue; // نوع ناشناخته در UI؛ نادیده گرفته می‌شود

    // ترتیب گره‌ها بر اساس core/cir/pin_order.py:
    //   voltage_source  -> [positive, negative]   (port2=+, port1=-)
    //   NPN/PNP         -> [collector, base, emitter]  (port2, port1, port3)
    //   NMOS/PMOS       -> [drain, gate, source, bulk=source]  (port2, port1, port3, port3)
    //   سایر دوپایه‌ها   -> [a, b]
    let nodes;
    if (comp.type === 'V' || comp.type === 'VAC' || comp.type === 'AM') {
      nodes = [String(comp.node2), String(comp.node1)];
    } else if (comp.type === 'NPN' || comp.type === 'PNP') {
      nodes = [String(comp.node2), String(comp.node1), String(comp.node3)];
    } else if (comp.type === 'NMOS' || comp.type === 'PMOS') {
      nodes = [String(comp.node2), String(comp.node1), String(comp.node3), String(comp.node3)];
    } else {
      nodes = [String(comp.node1), String(comp.node2)];
    }

    // برای VAC، مقدار SPICE باید SIN(offset amplitude freq) باشد
    let cirValue = comp.value === '' ? null : comp.value ?? null;
    if (comp.type === 'VAC') {
      const offset    = comp.vac_offset    ?? 0;
      const amplitude = comp.vac_amplitude ?? 1;
      const freq      = comp.vac_freq      ?? 1000;
      cirValue = `SIN(${offset} ${amplitude} ${freq})`;
    } else if (comp.type === 'VM') {
      // ولتمتر: مقاومت ۱ گیگاهم (بی‌نهایت عملی در SPICE)
      cirValue = '1G';
    } else if (comp.type === 'AM') {
      // آمپرمتر: منبع ولتاژ صفر ولت (اتصال کوتاه با جریان قابل اندازه‌گیری)
      cirValue = '0';
    }

    cirComponents.push({
      id: comp.name,
      type: cirType,
      value: cirValue,
      nodes,
      label: comp.name,
      properties: { x: comp.x, y: comp.y, rotation: comp.rotation },
    });
  }

  return {
    components: cirComponents,
    metadata: {
      ground_node: GROUND_NODE,
      ...(options.title ? { title: options.title } : {}),
    },
  };
}

/**
 * CIR -> مدل UI
 *
 * چیدمان (layout): اگر تمام المان‌های پشتیبانی‌شده properties.x/y عددی داشته
 * باشند (یعنی این CIR قبلاً از همین UI خروجی گرفته شده)، همان موقعیت‌ها حفظ
 * می‌شود. در غیر این صورت (مثلاً CIR تولیدشده توسط AI که موقعیت ندارد) یک
 * چیدمان خطی ساده از چپ به راست محاسبه می‌شود.
 *
 * @param {object} circuit CIR ورودی
 * @returns {{components: Array, wires: Array, nextNode: number, warnings: string[]}}
 */
export function cirToUiModel(circuit) {
  const warnings = [];
  const supported = [];

  for (const comp of circuit?.components ?? []) {
    const uiType = CIR_TO_UI_TYPE[comp.type];
    if (!uiType) {
      warnings.push(
        `المان ${comp.id} از نوع «${comp.type}» در ویرایشگر فعلی پشتیبانی نمی‌شود و نمایش داده نشد.`
      );
      continue;
    }
    if (!Array.isArray(comp.nodes) || comp.nodes.length < 2) {
      warnings.push(`المان ${comp.id} گره کافی ندارد و نادیده گرفته شد.`);
      continue;
    }
    supported.push({ ...comp, _uiType: uiType });
  }

  const allHavePositions = supported.length > 0 && supported.every(
    (c) => typeof c.properties?.x === 'number' && typeof c.properties?.y === 'number'
  );

  // اگر هیچ موقعیتی موجود نباشد (یعنی CIR از AI آمده)، چیدمان لایه‌ای محاسبه می‌شود
  const computedLayout = allHavePositions ? null : computeLayeredLayout(supported);

  const uiComponents = supported.map((comp) => {
    // معکوس نگاشت uiModelToCIR برای هر نوع المان
    let n1, n2, n3;
    if (comp._uiType === 'V') {
      // CIR: [positive, negative] → port1=negative, port2=positive
      n1 = comp.nodes[1]; n2 = comp.nodes[0];
    } else if (comp._uiType === 'NPN' || comp._uiType === 'PNP') {
      // CIR: [collector, base, emitter] → port1=base, port2=collector, port3=emitter
      n2 = comp.nodes[0]; n1 = comp.nodes[1]; n3 = comp.nodes[2];
    } else if (comp._uiType === 'NMOS' || comp._uiType === 'PMOS') {
      // CIR: [drain, gate, source, body] → port1=gate, port2=drain, port3=source
      n2 = comp.nodes[0]; n1 = comp.nodes[1]; n3 = comp.nodes[2];
    } else {
      n1 = comp.nodes[0]; n2 = comp.nodes[1];
    }

    const layout = allHavePositions
      ? comp.properties
      : { ...computedLayout.get(comp.id), rotation: 0 };

    const isThreePin = THREE_PIN_UI_TYPES.has(comp._uiType);
    return {
      id: uid('comp'),
      type: comp._uiType,
      prefix: UI_TYPE_PREFIX[comp._uiType] ?? comp._uiType,
      label: comp._uiType === 'V' ? 'منبع ولتاژ' : comp._uiType,
      name: comp.id,
      value: comp.value ?? '',
      node1: String(n1),
      node2: String(n2),
      ...(isThreePin && { node3: String(n3) }),
      x: layout.x,
      y: layout.y,
      rotation: layout.rotation ?? 0,
    };
  });

  // ساخت wireهای بصری: به‌جای زنجیر کردن همه‌ی پایه‌های هم‌گره به هم (که با
  // ۳+ المان روی یک گره باعث ترسیم خطوط بلند و روی‌هم‌افتاده می‌شود)، یک
  // نقطه‌ی hub مجازی برای هر گره با ۳+ اتصال در نظر می‌گیریم و میانگین
  // موقعیت پایه‌ها را به‌عنوان نقطه‌ی هاب فرض می‌کنیم؛ هر پایه مستقیم به این
  // میانگین (یعنی در عمل به نزدیک‌ترین پایه‌ی دیگر) وصل می‌شود. برای حالت
  // ساده (۲ اتصال روی هر گره، یعنی سری/موازی پایه) نتیجه با قبل یکسان است.
  const portsByNode = new Map();
  uiComponents.forEach((c, idx) => {
    const ports = [[c.node1, 1], [c.node2, 2]];
    if (c.node3 !== undefined) ports.push([c.node3, 3]);
    ports.forEach(([node, port]) => {
      if (!portsByNode.has(node)) portsByNode.set(node, []);
      portsByNode.get(node).push({ compIndex: idx, port });
    });
  });

  const uiWires = [];
  for (const ports of portsByNode.values()) {
    if (ports.length < 2) continue;

    // پایه‌ها را بر اساس فاصله‌ی y مرتب می‌کنیم تا خطوط به‌صورت منطقی
    // (نزدیک‌ترین به نزدیک‌ترین) وصل شوند، نه به ترتیب تصادفی ساخت.
    const withPos = ports.map((p) => ({
      ...p,
      pos: uiComponents[p.compIndex],
    }));
    withPos.sort((a, b) => (a.pos.y - b.pos.y) || (a.pos.x - b.pos.x));

    for (let i = 0; i < withPos.length - 1; i++) {
      const a = withPos[i];
      const b = withPos[i + 1];
      uiWires.push({
        id: uid('wire'),
        startCompId: uiComponents[a.compIndex].id,
        startNodeIndex: a.port,
        endCompId: uiComponents[b.compIndex].id,
        endNodeIndex: b.port,
      });
    }
  }

  // شماره گره بعدی، برای جلوگیری از تداخل هنگام افزودن المان جدید توسط کاربر
  let maxNode = 0;
  for (const node of portsByNode.keys()) {
    const n = parseInt(node, 10);
    if (!Number.isNaN(n) && n > maxNode) maxNode = n;
  }

  return {
    components: uiComponents,
    wires: uiWires,
    nextNode: maxNode + 1,
    warnings,
  };
}
