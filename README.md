# CircuPilot

> AI-Powered Electronic Circuit Design, Simulation, and Education Platform

CircuPilot is an AI-assisted electronic circuit design platform that combines Large Language Models (LLMs), a unified Circuit Intermediate Representation (CIR), SPICE netlist generation, schematic visualization, and circuit simulation.

This repository contains the **research prototype** developed for the academic version of the project.

The production version is under active private development and includes many additional features beyond this repository.

---

## 🌐 Live Demo

**Website**

https://circupilot.com

---

## Project Status

🟡 **Research Prototype**

This public repository represents the original research prototype used during the early development of CircuPilot and referenced by our research work.

The production platform is being actively developed in a private repository and currently includes features such as:

- User authentication
- Cloud deployment
- AI conversation history
- Circuit save/load
- Administration dashboard
- Usage analytics
- Rate limiting
- Continuous deployment
- Many architectural improvements

---

## Key Features

- AI-assisted circuit generation from natural language
- Unified Circuit Intermediate Representation (CIR)
- Automatic SPICE netlist generation
- Schematic visualization
- Circuit simulation using PySpice / ngspice
- React-based circuit editor
- FastAPI backend
- Docker deployment

---

# Project Architecture

```
ai-circuit-platform/
├── core/
│   ├── cir/
│   ├── interfaces/
│   └── llm/
│
├── services/
│   ├── text_to_cir/
│   ├── cir_to_spice/
│   └── schematic/
│
├── api/
│   └── main.py
│
├── frontend/
│   └── src/
│       ├── CircuitBuilder.jsx
│       └── lib/
│           ├── cir.js
│           └── api.js
│
└── tests/
```

---

# Screenshots

*(Screenshots of the latest CircuPilot interface will be added soon.)*

---

# Installation

## Option 1 — Docker (Recommended)

```bash
cp .env.example .env

# Configure your LLM_API_KEY

docker compose up --build
```

Backend:

```
http://localhost:8000/docs
```

Frontend:

```
http://localhost:5173
```

---

## Option 2 — Local Installation

### Backend

```bash
python -m venv .venv

source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env

uvicorn api.main:app --reload
```

Run deterministic tests:

```bash
pytest
```

---

### Frontend

```bash
cd frontend

npm install

cp .env.example .env

npm run dev
```

Open:

```
http://localhost:5173
```

---

# Workflow

1. The user describes a circuit in natural language.

Example:

> Design a 5V RLC low-pass filter.

2. The request is sent to:

```
/api/text-to-cir
```

3. The AI generates a valid CIR.

4. The frontend converts CIR into its internal UI model.

5. The editor renders the schematic.

6. Any circuit modification is converted back into CIR.

7. CIR is converted into a SPICE netlist through:

```
/api/cir-to-spice
```

8. The generated netlist is displayed to the user.

---

# Circuit Simulation

The **Analyze Circuit** button performs DC Operating Point analysis using:

- PySpice
- ngspice

Docker images already include ngspice.

For local Windows installations, install ngspice separately:

https://ngspice.sourceforge.io

or

```bash
conda install -c conda-forge ngspice
```

---

# Current Limitations

This research prototype currently supports:

- Resistors
- Capacitors
- Inductors
- Diodes
- Voltage sources

Advanced components such as:

- Transistors
- Operational amplifiers
- Integrated circuits

will be added in future versions.

Currently every new AI prompt rebuilds the complete circuit rather than incrementally modifying the existing design.

---

# Roadmap

Planned improvements include:

- AI Circuit Improver
- AC / Transient analysis
- Better automatic schematic layout
- Audio-to-Circuit
- Image-to-Circuit
- Online IoT Laboratory
- Educational workflow improvements

---

# Research

The associated research paper is currently under review on **arXiv**.

The paper link will be added here once it becomes publicly available.

---

# Repository Notice

This repository intentionally contains the original research prototype only.

The actively maintained production version of **CircuPilot** is developed privately.

---

# For Developers

When adding a new circuit component, synchronize updates across:

| Layer | Files |
|-------|-------|
| CIR Schema | `core/cir/schema.py`, `pin_order.py` |
| SPICE Generator | `services/cir_to_spice/basic_converter.py` |
| SPICE Parser | `services/cir_to_spice/spice_parser.py` |
| Backend Schematic | `services/schematic/schemdraw_generator.py` |
| Frontend Adapter | `frontend/src/lib/cir.js` |
| UI Symbols | `frontend/src/CircuitBuilder.jsx` |

---

# Citation

If this repository contributes to your research, please consider citing the associated paper once it becomes publicly available.

---

# Copyright

Copyright © 2026

Ali Hedayati Pirouzan

This repository is provided for research and educational purposes.

Commercial use, redistribution, or inclusion in commercial software requires permission from the author.