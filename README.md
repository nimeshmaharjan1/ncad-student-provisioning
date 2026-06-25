# NCAD Student Provisioning Automation System

## Overview
This repository contains an internal automation system for NCAD student provisioning workflows.  
It replaces manual Excel-based processes used to manage student account creation and updates across multiple institutional systems.

The system processes a single Quercus student export and generates structured output files for multiple platforms including LDAP, Canvas, Google Workspace, Library, and OpenAthens.

---

## Problem Statement
Current student provisioning is manual and fragmented across multiple systems, requiring repetitive Excel processing, duplication checks, and format conversions.

This system centralises that logic into a single controlled pipeline to:
- reduce manual errors
- standardise data handling
- ensure consistent formatting across systems
- improve maintainability and handover capability

---

## System Architecture

The system follows a 3-layer architecture:

1. **Frontend (Next.js)**
   - Upload Quercus CSV files
   - Trigger processing jobs
   - Download generated system-specific outputs

2. **Backend (FastAPI + Python)**
   - Core processing engine
   - Data cleaning and transformation
   - System-specific output generation

3. **Data Processing Layer (pandas)**
   - CSV parsing
   - Data normalization
   - Rule-based transformations

---

## Core Workflow

Quercus Export  
→ Canonical Student Dataset  
→ System Transformations  
→ Output Files per System

Outputs:
- LDAP import file
- Canvas SIS file
- Google Workspace provisioning file
- Library system file
- OpenAthens bulk upload file

---

## Repository Structure

- `/frontend` → Next.js UI
- `/backend` → FastAPI processing engine
- `/docs` → system documentation and SOPs
- `/samples` → example input/output CSVs
- `/scripts` → utility scripts (future use)

---

## MVP Scope

Current MVP includes:
- CSV upload (Quercus export)
- fixed-format data ingestion
- transformation into canonical dataset
- generation of system-specific CSV outputs

Excluded from MVP:
- direct API integrations with external systems
- automated login/download workflows
- database storage or audit system
- real-time syncing

---

## Data Handling Approach (MVP)

The system assumes:
- Quercus export format is stable
- column mapping is fixed and predefined
- transformations are deterministic and rule-based

This approach prioritises simplicity and rapid implementation.

---

## Future Enhancements

- dynamic column mapping for Quercus exports
- validation dashboard for error reporting
- database-backed audit trail
- API integrations with external systems
- role-based access control for staff usage

---

## Purpose

This system is designed as an internal NCAD IT provisioning tool and is intended for long-term maintainability and handover.