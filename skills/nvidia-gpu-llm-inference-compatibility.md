---
name: nvidia-gpu-llm-inference-compatibility
description: "Check NVIDIA GPU compute capability before installing drivers for LLM inference. Fermi (2.x) and older cannot run modern frameworks. Use when: (1) setting up a GPU for LLM inference, (2) choosing an NVIDIA driver version, (3) troubleshooting why a GPU is not accelerating inference, (4) evaluating whether a GPU upgrade is needed."
category: tooling
date: "2026-11-26"
version: "1.0.0"
user-invocable: false
tags: [nvidia, gpu, llm, inference, cuda, compute-capability, driver, fermi, compatibility]
---

# NVIDIA GPU Compatibility for LLM Inference

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-11-26 |
| **Objective** | Determine whether an NVIDIA GPU can accelerate LLM inference before investing in driver installation. |
| **Outcome** | Operational — compatibility matrix documented. |

## When to Use

- You are setting up a GPU for LLM inference (Ollama, vLLM, llama.cpp, etc.).
- You are choosing which NVIDIA driver version to install.
- A GPU is not accelerating inference and you need to diagnose why.
- You are evaluating whether a GPU upgrade is needed for LLM workloads.

## Verified Workflow

### Quick Reference

```bash
# Check GPU compute capability
nvidia-smi --query-gpu=name,compute_cap --format=csv,noheader

# Or look up the GPU model online:
# https://developer.nvidia.com/cuda-gpus

# Minimum for LLM inference: compute capability 3.5 (Kepler)
# Recommended: compute capability 7.0+ (Volta) for Tensor Cores
```

### Compatibility Matrix

| Architecture | Compute Cap | Last Driver | Last CUDA | LLM Inference? | Notes |
|-------------|-------------|-------------|-----------|----------------|-------|
| Fermi (GF1xx) | 2.0–2.1 | 470.xx | 11.4 | **No** | Driver 470 is last; no modern framework support |
| Kepler (GKxxx) | 3.0–3.7 | 470.xx | 11.4 | Marginal | Some frameworks support 3.5+; very slow |
| Maxwell (GMxxx) | 5.0–5.3 | 535+ | 12.x | Limited | Low VRAM; basic support |
| Pascal (GPxxx) | 6.0–6.2 | 535+ | 12.x | Yes | Minimum viable for LLM inference |
| Volta (GVxxx) | 7.0–7.2 | 550+ | 12.x | Yes | Tensor Cores; good for inference |
| Turing (TUxxx) | 7.5 | 550+ | 12.x | Yes | RTX 20xx series |
| Ampere (GAxxx) | 8.0–8.6 | 550+ | 12.x | Yes | RTX 30xx; recommended minimum |
| Ada Lovelace | 8.9 | 550+ | 12.x | Yes | RTX 40xx; best consumer option |

### Driver Selection Guide

| GPU Generation | Install This Driver | Do NOT Install |
|---------------|-------------------|----------------|
| Fermi (GF1xx) | 470.xx | 535+ (drops support) |
| Kepler (GKxxx) | 470.xx | 535+ (drops support) |
| Maxwell+ | 535+ or latest | — |

### The Problem

Installing a modern driver (535+) on an old GPU (Fermi/Kepler) results in:
1. **Driver fails to load** — the kernel module won't bind to the GPU
2. **nvidia-smi fails** — "couldn't communicate with the NVIDIA driver"
3. **No GPU acceleration** — system falls back to CPU-only or nouveau
4. **Wasted time** — package installs but provides no benefit

### Diagnostic Steps

```bash
# 1. Identify the GPU
lspci | grep -i 'vga\|3d\|display'

# 2. Check current driver (if any)
nvidia-smi 2>&1 | head -5
lsmod | grep nvidia

# 3. Look up compute capability
# https://developer.nvidia.com/cuda-gpus
# Or: nvidia-smi --query-gpu=compute_cap --format=csv,noheader (if driver loaded)

# 4. Check available drivers
apt-cache search nvidia-driver | sort -V | tail -10

# 5. Verify driver-GPU compatibility before installing
# Fermi/Kepler → 470.xx only
# Maxwell+ → 535+ (latest)
```

### Decision Rules

1. **Check compute capability first.** Before installing any driver, look up the GPU's compute capability. If it's below 3.5, LLM inference won't work regardless of driver.
2. **Match driver to architecture.** Fermi/Kepler → 470.xx. Maxwell+ → latest available (535+).
3. **Don't install modern drivers on old GPUs.** Driver 535+ will install but won't load on Fermi/Kepler.
4. **For LLM inference, VRAM matters more than driver.** A GPU with 4 GB VRAM (Kepler) is borderline; 8+ GB (Pascal+) is recommended; 12+ GB (Ampere+) is ideal.
5. **CPU-only is a valid fallback.** If the GPU can't accelerate LLM inference, tune the CPU (governor → performance, THP → always) instead.

### Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Install latest driver on old GPU | `apt install nvidia-driver-535` on GT 430 (Fermi) | Driver installed but kernel module won't load; nvidia-smi fails | Check compute capability first; Fermi needs 470.xx |
| Assume driver enables LLM inference | Installed 470 on GT 430 expecting CUDA acceleration | Driver works but GT 430 (compute cap 2.1, 1 GB VRAM) can't run any modern LLM framework | Driver ≠ inference capability; check framework requirements |
| Use nouveau as fallback | Rely on open-source nouveau driver | nouveau provides display but no CUDA/compute; no LLM acceleration | nouveau is display-only; proprietary driver needed for compute |

## Results & Parameters

### Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| Minimum compute cap for LLM | 3.5 (Kepler) | Some frameworks support 3.0+ but are very slow |
| Recommended compute cap | 7.0+ (Volta) | Tensor Cores significantly improve inference |
| Minimum VRAM for LLM | 4 GB | For small models (7B params) with quantization |
| Recommended VRAM | 12+ GB | For 13B+ models with comfortable headroom |
| Fermi last driver | 470.xx | R470 series |
| Fermi last CUDA | 11.4 | CUDA 11.4 |
| Kepler last driver | 470.xx | Same as Fermi |
| Maxwell+ driver | 535+ (latest) | Full support |

### Verification

```bash
# After driver install, verify GPU is recognized
nvidia-smi

# Check compute capability
nvidia-smi --query-gpu=name,compute_cap,memory.total --format=csv,noheader

# Test CUDA (if installed)
nvcc --version 2>/dev/null || echo "CUDA not installed"

# Check if LLM framework can use GPU
ollama run llama3.2 --verbose 2>&1 | grep -i 'gpu\|cuda\|vram' || echo "Ollama not installed or no GPU detected"
```