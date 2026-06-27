import React, { useState, useEffect, useRef, useCallback } from 'react';
import { uiModelToCIR, cirToUiModel } from './lib/cir';
import { textToCIR, cirToSpice, analyzeCircuit, improveCircuit, simulateCircuit, ApiError } from './lib/api';

// --- آیکون‌های داخلی ---
const IconBase = ({ children, className, ...props }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>{children}</svg>
);
const Trash2    = (p) => <IconBase {...p}><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></IconBase>;
const Send      = (p) => <IconBase {...p}><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></IconBase>;
const Activity  = (p) => <IconBase {...p}><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></IconBase>;
const Download  = (p) => <IconBase {...p}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></IconBase>;
const Settings  = (p) => <IconBase {...p}><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></IconBase>;
const RotateCw  = (p) => <IconBase {...p}><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></IconBase>;
const BrainCircuit = (p) => <IconBase {...p}><path d="M12 5V3"/><path d="m6 8-2-2 4-3 2 4 .5-1.5L12 8l1.5-2.5.5 1.5 2-4 4 3-2 2"/><path d="M12 21v-2"/><path d="m6 16-2 2 4 3 2-4 .5 1.5L12 16l1.5 2.5.5-1.5 2 4 4-3-2-2"/><rect x="2" y="8" width="20" height="8" rx="2"/></IconBase>;
const MessageSquare = (p) => <IconBase {...p}><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></IconBase>;
const Zap       = (p) => <IconBase {...p}><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></IconBase>;
const Undo2     = (p) => <IconBase {...p}><path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5v0a5.5 5.5 0 0 1-5.5 5.5H11"/></IconBase>;
const Wand2     = (p) => <IconBase {...p}><path d="m15 4-1 1"/><path d="m5 4 1 1"/><path d="m14 14 1 1"/><path d="m6 14-1 1"/><path d="M10 2v1"/><path d="M10 17v1"/><path d="m3 11-1 .5"/><path d="m17 11 1 .5"/><path d="M10 9a4 4 0 0 1 4 4l-8 8-4-4Z"/></IconBase>;
const Play      = (p) => <IconBase {...p}><polygon points="5 3 19 12 5 21 5 3"/></IconBase>;
const Square    = (p) => <IconBase {...p}><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/></IconBase>;
const TrendingUp = (p) => <IconBase {...p}><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></IconBase>;

const COMPONENT_TYPES = [
  { type: 'R',    label: 'مقاومت',          prefix: 'R', defaultVal: '1k',      pinCount: 2, toolbarLabel: 'R'    },
  { type: 'C',    label: 'خازن',            prefix: 'C', defaultVal: '1u',      pinCount: 2, toolbarLabel: 'C'    },
  { type: 'L',    label: 'سلف',             prefix: 'L', defaultVal: '1m',      pinCount: 2, toolbarLabel: 'L'    },
  { type: 'D',    label: 'دیود',            prefix: 'D', defaultVal: '1N4148',  pinCount: 2, toolbarLabel: 'D'    },
  { type: 'V',    label: 'منبع DC',         prefix: 'V', defaultVal: '5',       pinCount: 2, toolbarLabel: 'VDC'  },
  { type: 'VAC',  label: 'منبع AC (سینوسی)',prefix: 'V', defaultVal: '',        pinCount: 2, toolbarLabel: 'VAC',
    vac_amplitude: 5, vac_freq: 1000, vac_offset: 0 },
  { type: 'NPN',  label: 'BJT NPN',         prefix: 'Q', defaultVal: '2N2222',  pinCount: 3, toolbarLabel: 'NPN'  },
  { type: 'PNP',  label: 'BJT PNP',         prefix: 'Q', defaultVal: '2N2907',  pinCount: 3, toolbarLabel: 'PNP'  },
  { type: 'NMOS', label: 'MOSFET-N',        prefix: 'M', defaultVal: 'IRF530',  pinCount: 3, toolbarLabel: 'nMOS' },
  { type: 'PMOS', label: 'MOSFET-P',        prefix: 'M', defaultVal: 'IRF9530', pinCount: 3, toolbarLabel: 'pMOS' },
  { type: 'GND',  label: 'زمین (GND)',      prefix: 'G', defaultVal: '',        pinCount: 1, toolbarLabel: '⏚'   },
  { type: 'VM',   label: 'ولتمتر',          prefix: 'VM',defaultVal: '',        pinCount: 2, toolbarLabel: 'V☰'  },
  { type: 'AM',   label: 'آمپرمتر',         prefix: 'AM',defaultVal: '',        pinCount: 2, toolbarLabel: 'A☰'  },
  { type: 'Joint',label: 'اتصال',           prefix: 'J', defaultVal: '',        pinCount: 1, toolbarLabel: '·'    },
];

const isThreePin = (type) => ['NPN', 'PNP', 'NMOS', 'PMOS'].includes(type);
const isMeter    = (type) => type === 'VM' || type === 'AM';
const compHeight = (type) => (type === 'Joint' || type === 'GND') ? 28 : isThreePin(type) ? 60 : 30;

const MAX_HISTORY = 50;

export default function CircuitBuilder() {
  const [components, setComponents] = useState([]);
  const [wires, setWires]           = useState([]);
  const [spiceCode, setSpiceCode]   = useState('');
  const [selectedId, setSelectedId] = useState(null);

  // Undo history
  const history    = useRef([]);
  const historyIdx = useRef(-1);

  const [draggedId, setDraggedId]     = useState(null);
  const [dragOffset, setDragOffset]   = useState({ x: 0, y: 0 });
  const [drawingWire, setDrawingWire] = useState(null);
  const [mousePos, setMousePos]       = useState({ x: 0, y: 0 });

  const [messages, setMessages] = useState([
    { id: 1, role: 'assistant', text: 'سلام! مدار خود را توصیف کنید یا با ابزارهای سمت چپ بکشید.\n\nنمونه دستورات:\n• «یک فیلتر RLC بساز»\n• «مقاومت R1 را تغییر بده تا ولتاژ گره ۲ بیشتر بشه»' }
  ]);
  const [prompt, setPrompt]   = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisError, setAnalysisError]   = useState(null);
  const [analyzing, setAnalyzing]           = useState(false);
  const [analysisMode, setAnalysisMode]     = useState('dc'); // 'dc' | 'transient'

  // Simulation (transient) state
  const [simResult, setSimResult]       = useState(null);  // {time, node_voltages, branch_currents}
  const [simError, setSimError]         = useState(null);
  const [simRunning, setSimRunning]     = useState(false);
  const [simParams, setSimParams]       = useState({ endTime: 1e-3, stepTime: 1e-5 });
  const [simVisible, setSimVisible]     = useState([]);    // گره‌های انتخاب‌شده برای نمودار
  const simAbortRef = useRef(false);                        // برای Stop

  const nodeCounter  = useRef(1);
  const containerRef = useRef(null);

  const getNextNode = () => (nodeCounter.current++).toString();

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, loading]);

  // snapshot برای undo
  const saveSnapshot = useCallback(() => {
    const snap = {
      components: JSON.parse(JSON.stringify(components)),
      wires:      JSON.parse(JSON.stringify(wires)),
      nc:         nodeCounter.current,
    };
    history.current  = history.current.slice(0, historyIdx.current + 1);
    history.current.push(snap);
    if (history.current.length > MAX_HISTORY) history.current.shift();
    historyIdx.current = history.current.length - 1;
  }, [components, wires]);

  const undo = useCallback(() => {
    if (historyIdx.current <= 0) return;
    historyIdx.current -= 1;
    const snap = history.current[historyIdx.current];
    setComponents(JSON.parse(JSON.stringify(snap.components)));
    setWires(JSON.parse(JSON.stringify(snap.wires)));
    nodeCounter.current = snap.nc;
    setSelectedId(null);
    setDrawingWire(null);
  }, []);

  const createComponent = (typeDef, x, y, value) => ({
    id:    Date.now() + Math.random(),
    ...typeDef,
    name:  '',
    node1: typeDef.type === 'GND' ? '0' : getNextNode(),
    node2: (typeDef.pinCount >= 2 && typeDef.type !== 'GND') ? getNextNode() : undefined,
    ...(typeDef.pinCount === 3 ? { node3: getNextNode() } : {}),
    value, x, y, rotation: 0,
  });

  const getPortPosition = (comp, nodeIndex) => {
    if (comp.type === 'Joint') return { x: comp.x + 10, y: comp.y + 10 };
    if (comp.type === 'GND')   return { x: comp.x + 14, y: comp.y };

    const h  = compHeight(comp.type);
    const cx = comp.x + 30;
    const cy = comp.y + h / 2;
    let dx, dy;
    if (isThreePin(comp.type)) {
      if      (nodeIndex === 1) { dx = -30; dy = 0;   }
      else if (nodeIndex === 2) { dx =  15; dy = -20; }
      else                      { dx =  15; dy =  20; }
    } else {
      dx = nodeIndex === 1 ? -30 : 30;
      dy = 0;
    }
    const rad = (comp.rotation * Math.PI) / 180;
    return { x: cx + dx*Math.cos(rad) - dy*Math.sin(rad), y: cy + dx*Math.sin(rad) + dy*Math.cos(rad) };
  };

  const computeWirePath = (p1, p2) => {
    if (Math.abs(p1.x - p2.x) < 2 || Math.abs(p1.y - p2.y) < 2)
      return `M ${p1.x} ${p1.y} L ${p2.x} ${p2.y}`;
    const midX = (p1.x + p2.x) / 2;
    return `M ${p1.x} ${p1.y} L ${midX} ${p1.y} L ${midX} ${p2.y} L ${p2.x} ${p2.y}`;
  };

  // تشخیص intent: بهبود مدار موجود یا ساخت جدید
  const isImproveIntent = (text) => {
    const hasCircuit = components.filter(c => c.type !== 'Joint' && c.type !== 'GND').length > 0;
    if (!hasCircuit) return false;
    const keywords = ['تغییر بده','اصلاح کن','بهبود','بهینه','ولتاژ','جریان','نویز',
      'مقاومت را','خازن را','افزایش','کاهش','بیشتر کن','کمتر کن','این مدار',
      'مدار فعلی','همین مدار','modify','improve','change','adjust','increase',
      'decrease','reduce','noise','voltage','current'];
    const lower = text.toLowerCase();
    return keywords.some(k => lower.includes(k));
  };

  const buildNewCircuit = async (userText) => {
    const circuit = await textToCIR(userText);
    const result  = cirToUiModel(circuit);
    saveSnapshot();
    setComponents(result.components);
    setWires(result.wires);
    nodeCounter.current = result.nextNode;
    setSelectedId(null); setAnalysisResult(null);
    const notes = [...(circuit?.metadata?.validation_warnings ?? []), ...result.warnings];
    let text = 'مدار بر اساس توضیحات شما ساخته شد.';
    if (notes.length) text += '\n\n⚠️ ' + notes.join('\n⚠️ ');
    return text;
  };

  const improveExistingCircuit = async (userText) => {
    const cir = uiModelToCIR(components, { title: 'مدار فعلی' });
    const res  = await improveCircuit(cir, userText, analysisResult);
    const result = cirToUiModel(res.circuit);
    saveSnapshot();
    setComponents(result.components);
    setWires(result.wires);
    nodeCounter.current = result.nextNode;
    setSelectedId(null); setAnalysisResult(null);
    const notes = [...(res.warnings ?? []), ...result.warnings];
    let text = `✅ ${res.explanation}`;
    if (notes.length) text += '\n\n⚠️ ' + notes.join('\n⚠️ ');
    return text;
  };

  const processPrompt = async () => {
    if (!prompt.trim() || loading) return;
    const userText = prompt.trim();
    setMessages(prev => [...prev, { id: Date.now()+Math.random(), role: 'user', text: userText }]);
    setPrompt(''); setLoading(true);
    try {
      const reply = isImproveIntent(userText)
        ? await improveExistingCircuit(userText)
        : await buildNewCircuit(userText);
      setMessages(prev => [...prev, { id: Date.now()+Math.random(), role: 'assistant', text: reply }]);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : 'خطای ناشناخته‌ای رخ داد.';
      setMessages(prev => [...prev, { id: Date.now()+Math.random(), role: 'assistant', text: `❌ خطا: ${msg}` }]);
    } finally {
      setLoading(false);
    }
  };

  // اجرای یکپارچه — بر اساس toggle DC/Transient
  const run = async () => {
    const el = components.filter(c => c.type !== 'Joint' && c.type !== 'GND');
    if (el.length === 0 || analyzing || simRunning) return;

    if (analysisMode === 'dc') {
      setAnalyzing(true); setAnalysisError(null); setAnalysisResult(null);
      try {
        const cir = uiModelToCIR(components, { title: 'تحلیل DC' });
        const res = await analyzeCircuit(cir);
        setAnalysisResult(res.results);
      } catch (err) {
        setAnalysisError(err instanceof ApiError ? err.message : 'خطای ناشناخته');
      } finally { setAnalyzing(false); }
    } else {
      setSimRunning(true); setSimError(null); setSimResult(null);
      simAbortRef.current = false;
      try {
        const cir = uiModelToCIR(components, { title: 'شبیه‌سازی' });
        const res = await simulateCircuit(cir, {
          stepTime: simParams.stepTime,
          endTime:  simParams.endTime,
          maxPoints: 2000,
        });
        if (!simAbortRef.current) {
          setSimResult(res);
          const nodeNames = Object.keys(res.node_voltages).filter(n => n !== '0');
          setSimVisible(nodeNames.slice(0, 4));
        }
      } catch (err) {
        if (!simAbortRef.current)
          setSimError(err instanceof ApiError ? err.message : 'خطای ناشناخته');
      } finally { setSimRunning(false); }
    }
  };

  const stopSimulation = () => {
    simAbortRef.current = true;
    setSimRunning(false);
    setSimError('شبیه‌سازی توسط کاربر متوقف شد.');
  };

  // نام‌گذاری خودکار
  useEffect(() => {
    if (!components.some(c => c.name === '')) return;
    const counts = {};
    components.forEach(c => {
      if (c.name) { const m = c.name.match(/([A-Za-z]+)(\d+)/); if (m) counts[m[1]] = Math.max(counts[m[1]]||0, parseInt(m[2],10)); }
    });
    setComponents(prev => prev.map(c => {
      if (c.name) return c;
      if (c.type === 'Joint') return { ...c, name: `J${Math.floor(Math.random()*1000)}` };
      if (c.type === 'GND')   return { ...c, name: `GND${Math.floor(Math.random()*100)}` };
      const n = (counts[c.prefix]||0) + 1; counts[c.prefix] = n;
      return { ...c, name: `${c.prefix}${n}` };
    }));
  }, [components]);

  // تولید SPICE
  useEffect(() => {
    const el = components.filter(c => c.type !== 'Joint' && c.type !== 'GND');
    if (el.length === 0) { setSpiceCode(''); return; }
    if (el.some(c => c.name === '')) return;
    const cir = uiModelToCIR(components, { title: 'مدار طراحی‌شده در ویرایشگر' });
    if (!cir.components.length) { setSpiceCode(''); return; }
    const t = setTimeout(() => {
      cirToSpice(cir).then(r => setSpiceCode(r.spice))
        .catch(e => setSpiceCode(`* خطا:\n* ${e instanceof ApiError ? e.message : e}`));
    }, 400);
    return () => clearTimeout(t);
  }, [components]);

  // کیبورد
  const handleKeyDown = useCallback((e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'z') { e.preventDefault(); undo(); return; }
    if (e.key === 'Escape') { if (drawingWire) setDrawingWire(null); else setSelectedId(null); }
    if ((e.key === 'Delete'||e.key==='Backspace') && selectedId) {
      if (['INPUT','TEXTAREA'].includes(document.activeElement.tagName)) return;
      saveSnapshot(); removeComponent(selectedId);
    }
    if ((e.key==='r'||e.key==='R') && selectedId) {
      if (['INPUT','TEXTAREA'].includes(document.activeElement.tagName)) return;
      saveSnapshot(); rotateSelected();
    }
  }, [drawingWire, selectedId, undo, saveSnapshot]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  const getNodeByIndex = (comp, idx) => {
    if (idx===1) return comp.node1;
    if (idx===2) return comp.node2 ?? comp.node1;
    if (idx===3) return comp.node3 ?? comp.node1;
    return comp.node1;
  };

  const handleStageMouseDown = (e) => {
    if (!drawingWire) return;
    const rect = containerRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left, clickY = e.clientY - rect.top;
    const jType = COMPONENT_TYPES.find(c => c.type==='Joint');
    const startComp = components.find(c => c.id===drawingWire.startCompId);
    const activeNode = getNodeByIndex(startComp, drawingWire.startNodeIndex);
    const jId = Date.now()+Math.random();
    setComponents(prev => [...prev, { id:jId, ...jType, name:`J${prev.length}`, node1:activeNode, node2:undefined, value:'', x:clickX-10, y:clickY-10, rotation:0 }]);
    setWires(prev => [...prev, { id:Date.now()+Math.random(), startCompId:drawingWire.startCompId, startNodeIndex:drawingWire.startNodeIndex, endCompId:jId, endNodeIndex:1 }]);
    setDrawingWire({ startCompId:jId, startNodeIndex:1 });
  };

  const handleMouseMove = (e) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left, y = e.clientY - rect.top;
    setMousePos({ x, y });
    if (draggedId && !drawingWire)
      setComponents(prev => prev.map(c => c.id===draggedId ? {...c, x:x-dragOffset.x, y:y-dragOffset.y} : c));
  };

  const handleCompMouseDown = (e, comp) => {
    e.stopPropagation();
    if (drawingWire) return;
    setDraggedId(comp.id);
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      setDragOffset({ x:e.clientX-rect.left-comp.x, y:e.clientY-rect.top-comp.y });
    }
    setSelectedId(comp.id);
  };

  const wasDragged = useRef(false);

  const handleMouseUp = () => {
    if (draggedId) { saveSnapshot(); wasDragged.current = true; }
    else { wasDragged.current = false; }
    setDraggedId(null);
  };

  const handlePortClick = (e, compId, nodeIndex) => {
    e.stopPropagation();
    if (drawingWire) {
      if (drawingWire.startCompId===compId && drawingWire.startNodeIndex===nodeIndex) return;
      const sc = components.find(c=>c.id===drawingWire.startCompId);
      const ec = components.find(c=>c.id===compId);
      if (sc && ec) {
        saveSnapshot();
        setWires(prev => [...prev, { id:Date.now()+Math.random(), startCompId:drawingWire.startCompId, startNodeIndex:drawingWire.startNodeIndex, endCompId:compId, endNodeIndex:nodeIndex }]);
        const src = getNodeByIndex(sc, drawingWire.startNodeIndex);
        const tgt = getNodeByIndex(ec, nodeIndex);
        let winner=src, loser=tgt;
        if (tgt==='0' || (src!=='0' && parseInt(tgt)<parseInt(src))) { winner=tgt; loser=src; }
        if (winner!==loser) {
          setComponents(prev => prev.map(c => {
            let n1=c.node1, n2=c.node2, n3=c.node3;
            if (n1===loser) n1=winner; if (n2===loser) n2=winner; if (n3===loser) n3=winner;
            return {...c, node1:n1, node2:n2, node3:n3};
          }));
        }
      }
      setDrawingWire(null);
    } else {
      setDrawingWire({ startCompId:compId, startNodeIndex:nodeIndex });
    }
  };

  const addComponent = (compType) => {
    saveSnapshot();
    setComponents(prev => {
      const count = prev.filter(c=>c.type!=='Joint'&&c.type!=='GND').length;
      const x = 100 + (count%5)*90, y = 100 + Math.floor(count/5)*100;
      return [...prev, createComponent(compType, x, y, compType.defaultVal)];
    });
  };

  const removeComponent = (id) => {
    setComponents(prev => prev.filter(c=>c.id!==id));
    setWires(prev => prev.filter(w=>w.startCompId!==id&&w.endCompId!==id));
    if (selectedId===id) setSelectedId(null);
  };

  const rotateSelected = () => setComponents(prev => prev.map(c => c.id===selectedId ? {...c, rotation:(c.rotation+90)%360} : c));

  const clearAll = () => {
    saveSnapshot();
    setComponents([]); setWires([]); setSpiceCode('');
    setSelectedId(null); setAnalysisResult(null); setAnalysisError(null);
    nodeCounter.current = 1;
    setMessages([{ id:Date.now(), role:'assistant', text:'مدار پاک شد. منتظر توضیح شما هستم.' }]);
  };

  const renderSymbol = (comp) => {
    const clr = selectedId===comp.id ? '#3b82f6' : '#4b5563';
    const s   = { stroke:clr, strokeWidth:1.8, fill:'none' };
    if (comp.type==='Joint') return <circle cx="10" cy="10" r="4" fill="#4b5563"/>;
    if (comp.type==='GND')   return (
      <g stroke={clr} strokeWidth="1.8">
        <line x1="14" y1="0"  x2="14" y2="10"/>
        <line x1="4"  y1="10" x2="24" y2="10"/>
        <line x1="8"  y1="14" x2="20" y2="14"/>
        <line x1="11" y1="18" x2="17" y2="18"/>
      </g>
    );
    switch(comp.type) {
      case 'R': return <path d="M0,15 L10,15 L15,5 L25,25 L35,5 L45,25 L50,15 L60,15" {...s}/>;
      case 'C': return <g {...s}><line x1="0" y1="15" x2="25" y2="15"/><line x1="25" y1="5" x2="25" y2="25"/><line x1="35" y1="5" x2="35" y2="25"/><line x1="35" y1="15" x2="60" y2="15"/></g>;
      case 'L': return <path d="M0,15 L10,15 Q15,5 20,15 Q25,5 30,15 Q35,5 40,15 L50,15 L60,15" {...s}/>;
      case 'D': return <g {...s}><line x1="0" y1="15" x2="20" y2="15"/><line x1="40" y1="15" x2="60" y2="15"/><polygon points="20,5 20,25 40,15" fill="none" stroke={clr}/><line x1="40" y1="5" x2="40" y2="25"/></g>;
      case 'V': return <g {...s}><circle cx="30" cy="15" r="12"/><line x1="0" y1="15" x2="18" y2="15"/><line x1="42" y1="15" x2="60" y2="15"/><text x="24" y="19" fontSize="12" stroke="none" fill="#666" textAnchor="middle" fontWeight="bold">-</text><text x="36" y="19" fontSize="12" stroke="none" fill="#666" textAnchor="middle" fontWeight="bold">+</text></g>;
      case 'VAC': return <g {...s}><circle cx="30" cy="15" r="12"/><line x1="0" y1="15" x2="18" y2="15"/><line x1="42" y1="15" x2="60" y2="15"/><path d="M24,15 Q26,9 28,15 Q30,21 32,15 Q34,9 36,15" strokeWidth="1.5" fill="none" stroke={clr}/></g>;
      case 'VM': return (
        <g {...s}>
          <circle cx="30" cy="15" r="12" stroke={clr} fill="#f0fdf4"/>
          <line x1="0" y1="15" x2="18" y2="15"/><line x1="42" y1="15" x2="60" y2="15"/>
          <text x="30" y="19" fontSize="9" stroke="none" fill="#16a34a" textAnchor="middle" fontWeight="bold">V</text>
        </g>
      );
      case 'AM': return (
        <g {...s}>
          <circle cx="30" cy="15" r="12" stroke={clr} fill="#eff6ff"/>
          <line x1="0" y1="15" x2="18" y2="15"/><line x1="42" y1="15" x2="60" y2="15"/>
          <text x="30" y="19" fontSize="9" stroke="none" fill="#2563eb" textAnchor="middle" fontWeight="bold">A</text>
        </g>
      );
      case 'NPN': return <g {...s}><circle cx="26" cy="30" r="18"/><line x1="0" y1="30" x2="18" y2="30"/><line x1="18" y1="18" x2="18" y2="42"/><line x1="18" y1="22" x2="45" y2="10"/><line x1="18" y1="38" x2="45" y2="50"/><polygon points="34,46 28,48 30,41" fill={clr} stroke="none"/><text x="46" y="13" fontSize="7" fill="#6b7280" stroke="none">C</text><text x="46" y="54" fontSize="7" fill="#6b7280" stroke="none">E</text><text x="1" y="29" fontSize="7" fill="#6b7280" stroke="none">B</text></g>;
      case 'PNP': return <g {...s}><circle cx="26" cy="30" r="18"/><line x1="0" y1="30" x2="18" y2="30"/><line x1="18" y1="18" x2="18" y2="42"/><line x1="18" y1="22" x2="45" y2="10"/><line x1="18" y1="38" x2="45" y2="50"/><polygon points="22,40 27,37 29,44" fill={clr} stroke="none"/><text x="46" y="13" fontSize="7" fill="#6b7280" stroke="none">C</text><text x="46" y="54" fontSize="7" fill="#6b7280" stroke="none">E</text><text x="1" y="29" fontSize="7" fill="#6b7280" stroke="none">B</text></g>;
      case 'NMOS': return <g {...s}><line x1="0" y1="30" x2="16" y2="30"/><line x1="16" y1="16" x2="16" y2="44"/><line x1="21" y1="16" x2="21" y2="24"/><line x1="21" y1="28" x2="21" y2="32"/><line x1="21" y1="36" x2="21" y2="44"/><line x1="21" y1="20" x2="45" y2="10"/><line x1="21" y1="40" x2="45" y2="50"/><line x1="21" y1="30" x2="30" y2="30"/><polygon points="21,27 21,33 27,30" fill={clr} stroke="none"/><text x="46" y="13" fontSize="7" fill="#6b7280" stroke="none">D</text><text x="46" y="54" fontSize="7" fill="#6b7280" stroke="none">S</text><text x="1" y="29" fontSize="7" fill="#6b7280" stroke="none">G</text></g>;
      case 'PMOS': return <g {...s}><line x1="0" y1="30" x2="16" y2="30"/><line x1="16" y1="16" x2="16" y2="44"/><line x1="21" y1="16" x2="21" y2="24"/><line x1="21" y1="28" x2="21" y2="32"/><line x1="21" y1="36" x2="21" y2="44"/><line x1="21" y1="20" x2="45" y2="10"/><line x1="21" y1="40" x2="45" y2="50"/><line x1="21" y1="30" x2="30" y2="30"/><polygon points="30,27 30,33 24,30" fill={clr} stroke="none"/><text x="46" y="13" fontSize="7" fill="#6b7280" stroke="none">D</text><text x="46" y="54" fontSize="7" fill="#6b7280" stroke="none">S</text><text x="1" y="29" fontSize="7" fill="#6b7280" stroke="none">G</text></g>;
      default: return null;
    }
  };

  // محاسبه عدد نمایشی روی ولتمتر و آمپرمتر
  const getMeterReading = (comp) => {
    if (!isMeter(comp.type)) return null;
    const n1 = comp.node1, n2 = comp.node2;
    if (analysisResult && analysisMode === 'dc') {
      const v1 = analysisResult.node_voltages?.[String(n1)] ?? null;
      const v2 = analysisResult.node_voltages?.[String(n2)] ?? null;
      if (comp.type === 'VM' && v1 !== null && v2 !== null)
        return `${(v1 - v2).toFixed(3)} V`;
      if (comp.type === 'AM') {
        const cur = analysisResult.branch_currents?.[comp.name?.toLowerCase()];
        if (cur !== undefined && cur !== null) return `${Number(cur).toExponential(2)} A`;
        return '--- A';
      }
    }
    if (simResult && analysisMode === 'transient') {
      const arr1 = simResult.node_voltages?.[String(n1)];
      const arr2 = simResult.node_voltages?.[String(n2)];
      if (comp.type === 'VM' && arr1 && arr2) {
        const diffs = arr1.map((v,i) => v - (arr2[i] ?? 0));
        const pp = Math.max(...diffs) - Math.min(...diffs);
        return `${(pp/2).toFixed(3)} Vpp`;
      }
    }
    return '---';
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50 text-gray-800 font-sans" dir="rtl">
      <header className="bg-slate-900 text-white p-3 shadow-md z-30 flex justify-between gap-4">
        <div className="flex items-center gap-2">
          <BrainCircuit className="w-6 h-6 text-purple-400"/>
          <h1 className="text-lg font-bold">طراح مدار هوشمند</h1>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={undo} disabled={historyIdx.current <= 0} title="Ctrl+Z"
            className="text-xs bg-slate-700/80 hover:bg-slate-600 disabled:opacity-30 px-3 py-1 rounded text-white flex gap-1 items-center whitespace-nowrap">
            <Undo2 className="w-3 h-3"/> بازگشت
          </button>

          {/* Toggle DC / Transient */}
          <div className="flex rounded overflow-hidden border border-slate-600 text-xs">
            <button onClick={() => setAnalysisMode('dc')}
              className={`px-2 py-1 transition-colors ${analysisMode==='dc' ? 'bg-emerald-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'}`}>
              DC
            </button>
            <button onClick={() => setAnalysisMode('transient')}
              className={`px-2 py-1 transition-colors ${analysisMode==='transient' ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'}`}>
              Transient
            </button>
          </div>

          {/* Run / Stop */}
          {(!simRunning && !analyzing) ? (
            <button onClick={run}
              className={`text-xs px-3 py-1 rounded text-white flex gap-1 items-center whitespace-nowrap ${analysisMode==='dc' ? 'bg-emerald-600/80 hover:bg-emerald-600' : 'bg-blue-600/80 hover:bg-blue-600'}`}>
              <Play className="w-3 h-3"/> اجرا
            </button>
          ) : (
            <button onClick={stopSimulation}
              className="text-xs bg-orange-600 hover:bg-orange-700 px-3 py-1 rounded text-white flex gap-1 items-center whitespace-nowrap animate-pulse">
              <Square className="w-3 h-3"/> توقف
            </button>
          )}

          <button onClick={clearAll}
            className="text-xs bg-red-600/80 hover:bg-red-600 px-3 py-1 rounded text-white flex gap-1 items-center whitespace-nowrap">
            <Trash2 className="w-3 h-3"/> پاکسازی
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Toolbox */}
        <aside className="w-16 bg-white border-l border-gray-200 p-2 flex flex-col gap-2 shadow-sm z-20 overflow-y-auto items-center">
          {COMPONENT_TYPES.filter(c => c.type !== 'Joint').map(comp => (
            <button key={comp.type} onClick={() => addComponent(comp)} title={comp.label}
              className={`flex flex-col items-center gap-1 p-2 bg-gray-50 hover:bg-blue-50 hover:text-blue-700 border border-transparent hover:border-blue-200 rounded-lg transition-all text-xs w-full ${comp.type==='GND'?'border-green-200 bg-green-50/50':''}`}>
              <span className={`font-mono font-bold text-center leading-tight ${comp.type==='GND'?'text-xl text-green-700':comp.toolbarLabel.length>1?'text-[11px]':'text-lg'}`}>
                {comp.toolbarLabel}
              </span>
            </button>
          ))}
        </aside>

        {/* Canvas */}
        <main ref={containerRef}
          className="flex-1 bg-gray-100 relative overflow-hidden select-none cursor-crosshair"
          onMouseDown={handleStageMouseDown} onMouseMove={handleMouseMove} onMouseUp={handleMouseUp}
          style={{ backgroundImage:'radial-gradient(#cbd5e1 1px, transparent 1px)', backgroundSize:'20px 20px' }}>

          <svg className="absolute inset-0 w-full h-full pointer-events-none overflow-visible z-0">
            {wires.map(w => {
              const sc = components.find(c=>c.id===w.startCompId);
              const ec = components.find(c=>c.id===w.endCompId);
              if (!sc||!ec) return null;
              const p1 = getPortPosition(sc, w.startNodeIndex);
              const p2 = getPortPosition(ec, w.endNodeIndex);
              return <path key={w.id} d={computeWirePath(p1,p2)} stroke="#16a34a" strokeWidth="2" fill="none"/>;
            })}
            {drawingWire && (() => {
              const sc = components.find(c=>c.id===drawingWire.startCompId);
              if (!sc) return null;
              const p1 = getPortPosition(sc, drawingWire.startNodeIndex);
              return <path d={`M ${p1.x} ${p1.y} L ${mousePos.x} ${mousePos.y}`} stroke="#ef4444" strokeWidth="2" strokeDasharray="5,5" fill="none"/>;
            })()}
            {/* شماره گره‌ها */}
            {components.filter(c=>c.type!=='Joint'&&c.type!=='GND').flatMap(c => {
              const items = [];
              const addLabel = (pi, nd) => {
                if (nd==null) return;
                const pos = getPortPosition(c, pi);
                const tx = pi===1 ? pos.x-14 : pos.x+4;
                const ty = pi===3 ? pos.y+9  : pos.y-4;
                items.push(<text key={`nl-${c.id}-${pi}`} x={tx} y={ty} fontSize="7" fill="#f97316" fontFamily="monospace" style={{userSelect:'none',pointerEvents:'none'}}>{nd}</text>);
              };
              addLabel(1, c.node1); addLabel(2, c.node2);
              if (c.node3!==undefined) addLabel(3, c.node3);
              return items;
            })}
          </svg>

          {components.map(comp => {
            const isGND   = comp.type === 'GND';
            const isJoint = comp.type === 'Joint';
            const threePin = isThreePin(comp.type);
            const h = compHeight(comp.type);
            const portDot = <div className="w-2 h-2 mx-auto mt-1 rounded-full border border-red-500 bg-red-100"/>;
            const portHit = (idx) => (
              <div className="w-4 h-4 hover:bg-red-500/20 rounded-full cursor-crosshair z-30"
                onMouseDown={e=>e.stopPropagation()} onClick={e=>handlePortClick(e,comp.id,idx)}>
                {portDot}
              </div>
            );
            return (
              <div key={comp.id} onMouseDown={e=>handleCompMouseDown(e,comp)}
                style={{
                  left:comp.x, top:comp.y,
                  transform: (!isJoint&&!isGND) ? `rotate(${comp.rotation}deg)` : 'none',
                  transformOrigin: threePin?'30px 30px':isGND?'14px 14px':'30px 15px',
                  width: (isJoint||isGND)?`${h}px`:'60px',
                  height:`${h}px`,
                  cursor: drawingWire?'crosshair':'move',
                }}
                className="absolute z-10">
                {isJoint ? (
                  <div className="w-full h-full flex items-center justify-center cursor-crosshair"
                    onMouseDown={e=>e.stopPropagation()} onClick={e=>handlePortClick(e,comp.id,1)}>
                    <div className="w-3 h-3 bg-gray-600 rounded-full border-2 border-white shadow-sm hover:scale-125 transition-transform"/>
                  </div>
                ) : isGND ? (
                  <div className={`w-full h-full flex items-start justify-center rounded border ${selectedId===comp.id?'border-blue-400 bg-blue-50/30':'border-transparent'} ${drawingWire?'cursor-crosshair':'cursor-move'}`}
                    onClick={e=>{ if (!wasDragged.current) handlePortClick(e,comp.id,1); wasDragged.current=false; }}>
                    <svg width={h} height={h} viewBox={`0 0 ${h} ${h}`} className="pointer-events-none">{renderSymbol(comp)}</svg>
                  </div>
                ) : (
                  <div className={`w-full h-full bg-white/90 backdrop-blur border rounded transition-colors ${selectedId===comp.id?'border-blue-500 shadow-md ring-1 ring-blue-300':'border-gray-400'}`}>
                    <svg width="60" height={h} viewBox={`0 0 60 ${h}`} className="pointer-events-none absolute inset-0">{renderSymbol(comp)}</svg>
                    <div className="absolute left-[-8px] top-1/2 -translate-y-1/2">{portHit(1)}</div>
                    {threePin ? (
                      <>
                        <div className="absolute" style={{right:-8,top:2}}>{portHit(2)}</div>
                        <div className="absolute" style={{right:-8,top:42}}>{portHit(3)}</div>
                      </>
                    ) : (
                      <div className="absolute right-[-8px] top-1/2 -translate-y-1/2">{portHit(2)}</div>
                    )}
                    <div className="absolute top-full left-1/2 -translate-x-1/2 mt-1 text-[9px] font-mono bg-white/80 px-1 rounded border whitespace-nowrap pointer-events-none select-none z-40 shadow-sm">
                      <span className="font-bold text-blue-700">{comp.name}</span>
                      {isMeter(comp.type) ? (
                        <span className={`ml-1 font-bold ${comp.type==='VM'?'text-green-700':'text-blue-700'}`}>
                          {getMeterReading(comp)}
                        </span>
                      ) : (
                        <span className="text-gray-500"> {comp.value}</span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </main>

        {/* Right Sidebar */}
        <aside className="w-80 bg-white border-r border-gray-200 flex flex-col shadow-lg z-20">
          {/* Chat */}
          <div className="flex-[2] flex flex-col border-b min-h-[200px] bg-slate-50">
            <div className="bg-white p-2 border-b text-xs font-bold text-gray-500 flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-purple-500"/> دستیار هوشمند
              <span className="mr-auto text-[10px] text-gray-400 font-normal">ساخت / بهبود مدار</span>
              {loading && <Wand2 className="w-3 h-3 text-purple-400 animate-spin"/>}
            </div>
            <div className="flex-1 overflow-y-auto p-3 space-y-3 custom-scrollbar">
              {messages.map(msg => (
                <div key={msg.id} className={`flex ${msg.role==='user'?'justify-end':'justify-start'}`}>
                  <div className={`max-w-[85%] p-2 rounded-lg text-xs leading-relaxed whitespace-pre-line ${msg.role==='user'?'bg-blue-600 text-white rounded-br-none':'bg-white border border-gray-200 text-gray-700 rounded-bl-none shadow-sm'}`}>
                    {msg.text}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="max-w-[85%] p-2 rounded-lg text-xs bg-white border border-gray-200 text-gray-400 rounded-bl-none shadow-sm animate-pulse">در حال فکر کردن...</div>
                </div>
              )}
              <div ref={chatEndRef}/>
            </div>
            <div className="p-2 bg-white border-t flex gap-2">
              <input
                className="flex-1 bg-gray-100 border-0 rounded px-2 py-1 text-xs focus:ring-1 focus:ring-purple-500 outline-none disabled:opacity-50"
                placeholder="ساخت مدار جدید یا بهبود مدار موجود..."
                value={prompt} disabled={loading}
                onChange={e=>setPrompt(e.target.value)}
                onKeyDown={e=>e.key==='Enter'&&processPrompt()}
              />
              <button onClick={processPrompt} disabled={loading}
                className="bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white p-1 rounded transition-colors">
                <Send className="w-4 h-4"/>
              </button>
            </div>
          </div>

          {/* Properties */}
          <div className="flex-1 border-b bg-white flex flex-col min-h-[130px]">
            <div className="p-2 border-b text-xs font-bold text-gray-500 flex items-center gap-2 bg-gray-50">
              <Settings className="w-4 h-4"/> تنظیمات قطعه
            </div>
            <div className="p-3 flex-1 overflow-y-auto">
              {selectedId ? (() => {
                const c = components.find(i=>i.id===selectedId);
                if (!c) return <div className="text-center text-xs text-gray-400 mt-4">قطعه حذف شده</div>;
                const isGND = c.type==='GND';
                return (
                  <div className="space-y-3">
                    {!isGND && (
                      <div className="flex gap-2">
                        <div className="w-1/3"><label className="text-[9px] text-gray-400 block mb-1">نام</label>
                          <input value={c.name} onChange={e=>setComponents(prev=>prev.map(x=>x.id===c.id?{...x,name:e.target.value}:x))} className="w-full p-1 text-xs border rounded bg-gray-50"/></div>
                        <div className="w-2/3"><label className="text-[9px] text-gray-400 block mb-1">{c.type==='VAC'?'(auto)':'مقدار'}</label>
                          <input value={c.type==='VAC'?`SIN(${c.vac_offset??0} ${c.vac_amplitude??5} ${c.vac_freq??1000})`:c.value}
                            readOnly={c.type==='VAC'}
                            onChange={e=>setComponents(prev=>prev.map(x=>x.id===c.id?{...x,value:e.target.value}:x))}
                            className="w-full p-1 text-xs border rounded font-mono bg-gray-50"/></div>
                      </div>
                    )}
                    {c.type==='VAC' && (
                      <div className="space-y-1 bg-blue-50 p-2 rounded border border-blue-100">
                        <p className="text-[9px] text-blue-600 font-bold mb-1">تنظیمات منبع AC</p>
                        {[['dامنه (V)','vac_amplitude',5],['فرکانس (Hz)','vac_freq',1000],['آفست (V)','vac_offset',0]].map(([lbl,key,def])=>(
                          <div key={key} className="flex items-center gap-1">
                            <span className="text-[9px] text-gray-500 w-16">{lbl}</span>
                            <input type="number" value={c[key]??def}
                              onChange={e=>setComponents(prev=>prev.map(x=>x.id===c.id?{...x,[key]:Number(e.target.value)}:x))}
                              className="flex-1 p-0.5 text-xs border rounded font-mono"/>
                          </div>
                        ))}
                      </div>
                    )}
                    <div className="flex items-center justify-between bg-yellow-50 p-2 rounded border border-yellow-100 gap-1 flex-wrap">
                      <span className="text-[10px] text-yellow-800 font-mono">N1: {c.node1}</span>
                      {c.node2!==undefined && <span className="text-[10px] text-yellow-800 font-mono">N2: {c.node2}</span>}
                      {c.node3!==undefined && <span className="text-[10px] text-yellow-800 font-mono">N3: {c.node3}</span>}
                    </div>
                    {!isGND && <button onClick={()=>{saveSnapshot();rotateSelected();}}
                      className="w-full py-1 bg-blue-50 text-blue-600 rounded text-xs hover:bg-blue-100 flex items-center justify-center gap-1">
                      <RotateCw className="w-3 h-3"/> چرخش 90 درجه
                    </button>}
                    <button onClick={()=>{saveSnapshot();removeComponent(selectedId);}}
                      className="w-full py-1 bg-red-50 text-red-600 rounded text-xs hover:bg-red-100 flex items-center justify-center gap-1">
                      <Trash2 className="w-3 h-3"/> حذف قطعه
                    </button>
                  </div>
                );
              })() : (
                <div className="h-full flex flex-col items-center justify-center text-gray-300 gap-2">
                  <Settings className="w-8 h-8 opacity-20"/>
                  <span className="text-xs">یک قطعه را انتخاب کنید</span>
                </div>
              )}
            </div>
          </div>

          {/* Analysis Results */}
          {(analysisResult || analysisError) && (
            <div className="border-b bg-white max-h-44 overflow-y-auto custom-scrollbar">
              <div className="p-2 border-b text-xs font-bold text-gray-500 flex items-center justify-between bg-gray-50">
                <span className="flex items-center gap-2"><Zap className="w-4 h-4 text-emerald-600"/> نتایج تحلیل DC</span>
                <button onClick={()=>{setAnalysisResult(null);setAnalysisError(null);}} className="text-gray-400 hover:text-gray-600 text-[10px]">بستن</button>
              </div>
              <div className="p-3">
                {analysisError ? (
                  <p className="text-xs text-red-600 leading-relaxed whitespace-pre-line">{analysisError}</p>
                ) : (
                  <div className="space-y-2 text-xs font-mono">
                    <div><span className="text-gray-400">ولتاژ گره‌ها:</span>
                      <ul className="mt-1 space-y-0.5">
                        {Object.entries(analysisResult.node_voltages||{}).map(([n,v])=>(
                          <li key={n} className="text-gray-700">گره {n}: <span className="text-blue-600">{Number(v).toFixed(3)} V</span></li>
                        ))}
                      </ul>
                    </div>
                    {Object.keys(analysisResult.branch_currents||{}).length>0 && (
                      <div><span className="text-gray-400">جریان شاخه‌ها:</span>
                        <ul className="mt-1 space-y-0.5">
                          {Object.entries(analysisResult.branch_currents).map(([b,i])=>(
                            <li key={b} className="text-gray-700">{b}: <span className="text-purple-600">{Number(i).toExponential(3)} A</span></li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Simulation Params */}
          <div className="border-b bg-slate-50 px-3 py-2 flex items-center gap-2 flex-wrap">
            <TrendingUp className="w-3 h-3 text-blue-500 shrink-0"/>
            <span className="text-[10px] text-gray-500 font-bold">Transient:</span>
            <div className="flex items-center gap-1">
              <span className="text-[9px] text-gray-400">t پایان</span>
              <input type="number" step="any" value={simParams.endTime}
                onChange={e=>setSimParams(p=>({...p,endTime:Number(e.target.value)}))}
                className="w-16 p-0.5 text-[10px] border rounded font-mono bg-white"/>
              <span className="text-[9px] text-gray-400">s</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-[9px] text-gray-400">گام</span>
              <input type="number" step="any" value={simParams.stepTime}
                onChange={e=>setSimParams(p=>({...p,stepTime:Number(e.target.value)}))}
                className="w-16 p-0.5 text-[10px] border rounded font-mono bg-white"/>
              <span className="text-[9px] text-gray-400">s</span>
            </div>
          </div>

          {/* Oscilloscope */}
          {(simResult || simError || simRunning) && (
            <div className="border-b bg-white flex flex-col" style={{minHeight:'160px',maxHeight:'260px'}}>
              <div className="p-2 border-b text-xs font-bold text-gray-500 flex items-center justify-between bg-gray-50">
                <span className="flex items-center gap-2"><TrendingUp className="w-4 h-4 text-blue-500"/> اسیلوسکوپ</span>
                <button onClick={()=>{setSimResult(null);setSimError(null);}} className="text-gray-400 hover:text-gray-600 text-[10px]">بستن</button>
              </div>
              {simRunning && <div className="flex-1 flex items-center justify-center text-xs text-blue-500 animate-pulse">در حال شبیه‌سازی...</div>}
              {simError && <p className="p-3 text-xs text-red-600 whitespace-pre-line leading-relaxed">{simError}</p>}
              {simResult && !simRunning && (() => {
                const allNodes = Object.keys(simResult.node_voltages).filter(n=>n!=='0');
                const COLORS = ['#3b82f6','#ef4444','#22c55e','#f97316','#a855f7','#06b6d4'];
                const time = simResult.time;
                // نمونه‌برداری برای رسم نمودار ساده با SVG (بدون Recharts)
                const W=280, H=100, PAD=4;
                const allVals = simVisible.flatMap(n=>simResult.node_voltages[n]??[]);
                const minV = allVals.length ? Math.min(...allVals) : -1;
                const maxV = allVals.length ? Math.max(...allVals) :  1;
                const rangeV = (maxV-minV) || 1;
                const maxT = time[time.length-1] || 1;
                const toX = t => PAD + (t/maxT)*(W-2*PAD);
                const toY = v => PAD + (1-(v-minV)/rangeV)*(H-2*PAD);
                const makePath = (vals) => {
                  const pts = vals.map((v,i)=>`${toX(time[i]).toFixed(1)},${toY(v).toFixed(1)}`);
                  return 'M'+pts.join('L');
                };
                return (
                  <div className="p-2 flex-1 overflow-y-auto">
                    {/* گره selector */}
                    <div className="flex flex-wrap gap-1 mb-2">
                      {allNodes.map((n,i)=>(
                        <button key={n} onClick={()=>setSimVisible(prev=>prev.includes(n)?prev.filter(x=>x!==n):[...prev,n])}
                          className={`text-[9px] px-1.5 py-0.5 rounded border font-mono transition-colors ${simVisible.includes(n)?'text-white border-transparent':'bg-gray-50 border-gray-200 text-gray-400'}`}
                          style={simVisible.includes(n)?{backgroundColor:COLORS[i%COLORS.length]}:{}}>
                          گره {n}
                        </button>
                      ))}
                    </div>
                    {/* نمودار SVG */}
                    <svg width={W} height={H} className="bg-gray-950 rounded w-full" viewBox={`0 0 ${W} ${H}`}>
                      <line x1={PAD} y1={toY(0)} x2={W-PAD} y2={toY(0)} stroke="#374151" strokeWidth="0.5" strokeDasharray="2,2"/>
                      {simVisible.map((n,i)=>(
                        <path key={n} d={makePath(simResult.node_voltages[n]??[])}
                          stroke={COLORS[i%COLORS.length]} strokeWidth="1.2" fill="none"/>
                      ))}
                      <text x={PAD+2} y={PAD+8} fontSize="6" fill="#6b7280">{maxV.toFixed(2)}V</text>
                      <text x={PAD+2} y={H-PAD-2} fontSize="6" fill="#6b7280">{minV.toFixed(2)}V</text>
                      <text x={W-PAD-2} y={H-2} fontSize="6" fill="#6b7280" textAnchor="end">{(maxT*1000).toFixed(1)}ms</text>
                    </svg>
                    <p className="text-[9px] text-gray-400 mt-1">{time.length} نقطه — روی گره‌ها کلیک کنید تا نمایش/مخفی شوند</p>
                  </div>
                );
              })()}
            </div>
          )}

          {/* SPICE Netlist */}
          <div className="flex-1 flex flex-col bg-slate-900 text-white min-h-[120px]">
            <div className="flex justify-between items-center p-2 bg-slate-800 border-b border-slate-700">
              <span className="text-xs font-mono text-green-400 flex items-center gap-1"><Activity className="w-3 h-3"/> Netlist</span>
              <button onClick={()=>navigator.clipboard.writeText(spiceCode)} className="text-[10px] text-slate-400 hover:text-white flex gap-1"><Download className="w-3 h-3"/> کپی</button>
            </div>
            <textarea readOnly value={spiceCode} className="flex-1 bg-transparent text-[10px] font-mono text-green-300 resize-none focus:outline-none leading-relaxed p-2 custom-scrollbar" dir="ltr"/>
          </div>
        </aside>
      </div>
    </div>
  );
}
