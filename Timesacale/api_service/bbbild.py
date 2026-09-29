# -*- coding: utf-8 -*-
"""
Intelligent GPS Telemetry Fault Detection System
Technical Architecture Specification & Team Review Document
Standard: Executive Black & White / Grayscale Architecture Review
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    NextPageTemplate, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas as pdfcanvas

# Import vector diagram generators
from diagram_generators import (
    create_diagram_a, create_diagram_b, create_diagram_c, create_diagram_d
)

# ---------------------------------------------------------------------------
# PALETTE (Black & White / Clean Architectural Grayscale)
# ---------------------------------------------------------------------------
INK = colors.HexColor("#111111")
GREY_900 = colors.HexColor("#222222")
GREY_800 = colors.HexColor("#333333")
GREY_700 = colors.HexColor("#555555")
GREY_500 = colors.HexColor("#888888")
GREY_300 = colors.HexColor("#CCCCCC")
GREY_150 = colors.HexColor("#EAEAEA")
GREY_100 = colors.HexColor("#F5F5F5")
WHITE = colors.white
RULE_COLOR = colors.HexColor("#B0B0B0")

PAGE_W, PAGE_H = A4
MARGIN_L = 20 * mm
MARGIN_R = 20 * mm
MARGIN_T = 20 * mm
MARGIN_B = 20 * mm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R

DOC_TITLE = "Intelligent GPS Telemetry Fault Detection System"
DOC_SUB = "Bad Data Detection · Device Fault Detection · Architecture & Implementation Guide"
DOC_CODE = "RFC-ARCH-FDS-2026-01"
DOC_STATUS = "Architecture Review Board — Technical Specification"
TARGET_FLEET = "Concox/Jimi VL149 · Teltonika FMC125/650 · iTriangle Bharat 101"

# ---------------------------------------------------------------------------
# STYLES
# ---------------------------------------------------------------------------
styles = getSampleStyleSheet()

def pstyle(name, **kw):
    base = dict(fontName="Helvetica", fontSize=8.8, leading=12.8, textColor=INK,
                spaceAfter=4, alignment=TA_LEFT)
    base.update(kw)
    return ParagraphStyle(name, **base)

S_H1 = pstyle("H1", fontName="Helvetica-Bold", fontSize=14.5, leading=17,
              textColor=INK, spaceBefore=2, spaceAfter=6, alignment=TA_LEFT)
S_H2 = pstyle("H2", fontName="Helvetica-Bold", fontSize=10.5, leading=13.5,
              textColor=INK, spaceBefore=8, spaceAfter=4, alignment=TA_LEFT)
S_H3 = pstyle("H3", fontName="Helvetica-Bold", fontSize=9.0, leading=12,
              textColor=GREY_900, spaceBefore=6, spaceAfter=3, alignment=TA_LEFT)
S_BODY = pstyle("BODY", alignment=TA_JUSTIFY)
S_BODY_L = pstyle("BODY_L", alignment=TA_LEFT)
S_SMALL = pstyle("SMALL", fontSize=7.6, leading=10.5, textColor=GREY_700, alignment=TA_LEFT)
S_CAPTION = pstyle("CAPTION", fontName="Helvetica-Oblique", fontSize=7.6, leading=10.5,
                    textColor=GREY_700, alignment=TA_CENTER, spaceBefore=3, spaceAfter=6)
S_KICKER = pstyle("KICKER", fontName="Helvetica-Bold", fontSize=7.6, leading=9.5,
                   textColor=GREY_700, alignment=TA_LEFT, spaceAfter=2)

S_TBL_HDR = ParagraphStyle("TBLHDR", fontName="Helvetica-Bold", fontSize=7.8,
                            leading=10, textColor=WHITE, alignment=TA_LEFT)
S_TBL_HDR_C = ParagraphStyle("TBLHDRC", fontName="Helvetica-Bold", fontSize=7.8,
                              leading=10, textColor=WHITE, alignment=TA_CENTER)
S_TBL = ParagraphStyle("TBL", fontName="Helvetica", fontSize=7.6, leading=10.2,
                        textColor=INK, alignment=TA_LEFT)
S_TBL_C = ParagraphStyle("TBLC", fontName="Helvetica", fontSize=7.6, leading=10.2,
                          textColor=INK, alignment=TA_CENTER)
S_TBL_BOLD = ParagraphStyle("TBLB", fontName="Helvetica-Bold", fontSize=7.6, leading=10.2,
                             textColor=INK, alignment=TA_LEFT)
S_TBL_MONO = ParagraphStyle("TBLMONO", fontName="Courier", fontSize=7.2, leading=9.8,
                             textColor=GREY_900, alignment=TA_LEFT)

S_NOTE_LABEL = ParagraphStyle("NOTELBL", fontName="Helvetica-Bold", fontSize=7.8,
                                leading=10, textColor=WHITE, alignment=TA_LEFT)
S_NOTE_BODY = ParagraphStyle("NOTEBODY", fontName="Helvetica", fontSize=7.8,
                              leading=11, textColor=GREY_900, alignment=TA_LEFT)
S_PRINCIPLE_NUM = ParagraphStyle("PNUM", fontName="Helvetica-Bold", fontSize=12,
                                  leading=14, textColor=GREY_500, alignment=TA_CENTER)
S_PRINCIPLE_TXT = ParagraphStyle("PTXT", fontName="Helvetica", fontSize=8.4,
                                  leading=12, textColor=INK, alignment=TA_LEFT)
S_TOC_NUM = ParagraphStyle("TOCNUM", fontName="Helvetica-Bold", fontSize=8.6, leading=15,
                            textColor=GREY_800, alignment=TA_LEFT)
S_TOC_TITLE = ParagraphStyle("TOCTITLE", fontName="Helvetica", fontSize=8.6, leading=15,
                              textColor=INK, alignment=TA_LEFT)
S_TOC_PAGE = ParagraphStyle("TOCPAGE", fontName="Helvetica-Bold", fontSize=8.6, leading=15,
                             textColor=GREY_700, alignment=TA_RIGHT)

# ---------------------------------------------------------------------------
# REUSABLE FLOWABLE BLOCKS
# ---------------------------------------------------------------------------
def rule(width=1, color=RULE_COLOR, space_before=2, space_after=6):
    return HRFlowable(width="100%", thickness=width, color=color,
                      spaceBefore=space_before, spaceAfter=space_after, lineCap='round')

def kicker_heading(kicker, title):
    return [
        Paragraph(kicker.upper(), S_KICKER),
        Paragraph(title, S_H1),
        rule()
    ]

def note_box(label_text, body_text):
    t = Table([[Paragraph(label_text, S_NOTE_LABEL)],
               [Paragraph(body_text, S_NOTE_BODY)]],
              colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), GREY_900),
        ("BACKGROUND", (0, 1), (0, 1), GREY_100),
        ("TOPPADDING", (0, 0), (0, 0), 2.5),
        ("BOTTOMPADDING", (0, 0), (0, 0), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 1), (0, 1), 4),
        ("BOTTOMPADDING", (0, 1), (0, 1), 4.5),
        ("BOX", (0, 0), (-1, -1), 0.75, GREY_900),
    ]))
    return t

def data_table(headers, rows, col_widths, header_center=None, body_center_cols=None,
               mono_cols=None, zebra=True):
    header_center = header_center or []
    body_center_cols = body_center_cols or []
    mono_cols = mono_cols or []
    data = []
    hdr_row = []
    for i, h in enumerate(headers):
        st = S_TBL_HDR_C if i in header_center else S_TBL_HDR
        hdr_row.append(Paragraph(h, st))
    data.append(hdr_row)
    for r in rows:
        row = []
        for i, cell in enumerate(r):
            if i in mono_cols:
                st = S_TBL_MONO
            elif i in body_center_cols:
                st = S_TBL_C
            else:
                st = S_TBL
            row.append(Paragraph(str(cell), st))
        data.append(row)

    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), GREY_900),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("LINEBELOW", (0, 0), (-1, 0), 1, GREY_900),
        ("TOPPADDING", (0, 0), (-1, 0), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 3.5),
        ("TOPPADDING", (0, 1), (-1, -1), 2.8),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 2.8),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 1), (-1, -2), 0.4, GREY_300),
        ("BOX", (0, 0), (-1, -1), 0.75, GREY_900),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    if zebra:
        for i in range(1, len(data)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), GREY_100))
    t.setStyle(TableStyle(style))
    return t

# ---------------------------------------------------------------------------
# NUMBERED CANVAS (Running Headers & Footers on Interior Pages Only)
# ---------------------------------------------------------------------------
class ArchitectureCanvas(pdfcanvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            page_num = self._pageNumber
            # Suppress headers and footers on cover page
            if page_num > 1:
                self.draw_header()
                self.draw_footer(page_num, num_pages)
            pdfcanvas.Canvas.showPage(self)
        pdfcanvas.Canvas.save(self)

    def draw_header(self):
        self.saveState()
        self.setStrokeColor(RULE_COLOR)
        self.setLineWidth(0.6)
        self.line(MARGIN_L, PAGE_H - MARGIN_T + 8, PAGE_W - MARGIN_R, PAGE_H - MARGIN_T + 8)
        self.setFont("Helvetica-Bold", 7.8)
        self.setFillColor(GREY_900)
        self.drawString(MARGIN_L, PAGE_H - MARGIN_T + 13, "GPS TELEMETRY FAULT DETECTION SYSTEM")
        self.setFont("Helvetica", 7.6)
        self.setFillColor(GREY_700)
        self.drawRightString(PAGE_W - MARGIN_R, PAGE_H - MARGIN_T + 13, "Architecture Review Specification")
        self.restoreState()

    def draw_footer(self, page_num, total_pages):
        self.saveState()
        self.setStrokeColor(RULE_COLOR)
        self.setLineWidth(0.6)
        self.line(MARGIN_L, MARGIN_B - 6, PAGE_W - MARGIN_R, MARGIN_B - 6)
        self.setFont("Helvetica", 7.5)
        self.setFillColor(GREY_700)
        self.drawString(MARGIN_L, MARGIN_B - 16, f"{DOC_CODE}  ·  CONFIDENTIAL")
        self.drawCentredString(PAGE_W / 2, MARGIN_B - 16, "Architecture Team Discussion · Fleet IoT Platform")
        self.drawRightString(PAGE_W - MARGIN_R, MARGIN_B - 16, f"Page {page_num} of {total_pages}")
        self.restoreState()

def cover_decorator(canvas_obj, doc):
    canvas_obj.saveState()
    # Top banner
    canvas_obj.setFillColor(INK)
    canvas_obj.rect(0, PAGE_H - 72, PAGE_W, 72, fill=1, stroke=0)
    canvas_obj.setFillColor(WHITE)
    canvas_obj.setFont("Helvetica-Bold", 9)
    canvas_obj.drawString(MARGIN_L, PAGE_H - 30, "TECHNICAL ARCHITECTURE & SPECIFICATION")
    canvas_obj.setFont("Helvetica", 8.2)
    canvas_obj.drawRightString(PAGE_W - MARGIN_R, PAGE_H - 30, DOC_CODE)
    canvas_obj.setFont("Helvetica", 7.6)
    canvas_obj.setFillColor(colors.HexColor("#D0D0D0"))
    canvas_obj.drawString(MARGIN_L, PAGE_H - 45, "Distributed Telemetry Ingestion · Multi-Device Validation · Silence Watchdog")

    # Bottom footer line on cover
    canvas_obj.setStrokeColor(RULE_COLOR)
    canvas_obj.setLineWidth(0.6)
    canvas_obj.line(MARGIN_L, 34, PAGE_W - MARGIN_R, 34)
    canvas_obj.setFont("Helvetica", 7.6)
    canvas_obj.setFillColor(GREY_700)
    canvas_obj.drawString(MARGIN_L, 22, "Prepared for Internal Architecture Review & Sign-Off")
    canvas_obj.drawRightString(PAGE_W - MARGIN_R, 22, "Confidential — Internal Engineering Use Only")
    canvas_obj.restoreState()

# Document Template Setup
PDF_OUT_PATH = "/Users/sibikumar/Desktop/Timesacale/api_service/Intelligent_Fault_Detection_System_Professional.pdf"
doc = BaseDocTemplate(
    PDF_OUT_PATH,
    pagesize=A4,
    leftMargin=MARGIN_L, rightMargin=MARGIN_R, topMargin=MARGIN_T, bottomMargin=MARGIN_B,
    title=DOC_TITLE, author="Architecture Team", subject="Telemetry Fault Detection Design"
)

frame_cover = Frame(MARGIN_L, MARGIN_B + 10, CONTENT_W, PAGE_H - MARGIN_T - MARGIN_B - 60, id="cover_frame",
                    leftPadding=0, rightPadding=0, topPadding=10, bottomPadding=0)
frame_body = Frame(MARGIN_L, MARGIN_B, CONTENT_W, PAGE_H - MARGIN_T - MARGIN_B, id="body_frame",
                   leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

doc.addPageTemplates([
    PageTemplate(id="Cover", frames=[frame_cover], onPage=cover_decorator),
    PageTemplate(id="Body", frames=[frame_body]),
])

# ---------------------------------------------------------------------------
# DOCUMENT CONTENT GENERATION
# ---------------------------------------------------------------------------
story = []

# ===========================================================================
# PAGE 1: COVER PAGE
# ===========================================================================
story.append(Spacer(1, 35))
story.append(Paragraph(DOC_TITLE, ParagraphStyle(
    "CoverTitle", fontName="Helvetica-Bold", fontSize=24, leading=29,
    textColor=INK, alignment=TA_LEFT)))
story.append(Spacer(1, 8))
story.append(Paragraph(DOC_SUB, ParagraphStyle(
    "CoverSub", fontName="Helvetica", fontSize=11.5, leading=15.5,
    textColor=GREY_700, alignment=TA_LEFT)))
story.append(Spacer(1, 14))
story.append(HRFlowable(width="30%", thickness=2.2, color=INK, spaceAfter=16, hAlign="LEFT"))

meta_table_data = [
    [Paragraph("Document ID", ParagraphStyle("k", fontName="Helvetica-Bold", fontSize=8.2, textColor=GREY_800)),
     Paragraph(DOC_CODE, ParagraphStyle("v", fontName="Helvetica", fontSize=8.2, textColor=INK))],
    [Paragraph("Status / Phase", ParagraphStyle("k", fontName="Helvetica-Bold", fontSize=8.2, textColor=GREY_800)),
     Paragraph(DOC_STATUS, ParagraphStyle("v", fontName="Helvetica", fontSize=8.2, textColor=INK))],
    [Paragraph("Target Fleet", ParagraphStyle("k", fontName="Helvetica-Bold", fontSize=8.2, textColor=GREY_800)),
     Paragraph(TARGET_FLEET, ParagraphStyle("v", fontName="Helvetica", fontSize=8.2, textColor=INK))],
    [Paragraph("Infrastructure", ParagraphStyle("k", fontName="Helvetica-Bold", fontSize=8.2, textColor=GREY_800)),
     Paragraph("AWS IoT Core · AWS Lambda (Python 3.12) · TimescaleDB · AWS EventBridge · SNS",
               ParagraphStyle("v", fontName="Helvetica", fontSize=8.2, textColor=INK))],
    [Paragraph("Target Audience", ParagraphStyle("k", fontName="Helvetica-Bold", fontSize=8.2, textColor=GREY_800)),
     Paragraph("Architecture Review Board · Cloud Platform Engineering · SRE / Fleet Ops",
               ParagraphStyle("v", fontName="Helvetica", fontSize=8.2, textColor=INK))],
    [Paragraph("Review Scope", ParagraphStyle("k", fontName="Helvetica-Bold", fontSize=8.2, textColor=GREY_800)),
     Paragraph("Dual-Layer Ingestion Validation · Vehicle Master Sensor Check · 3-Scan Silence Watchdog · Fleet Telemetry Pipeline",
               ParagraphStyle("v", fontName="Helvetica", fontSize=8.2, textColor=INK))],
]
meta_t = Table(meta_table_data, colWidths=[35 * mm, 120 * mm])
meta_t.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 3.5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ("LINEBELOW", (0, 0), (-1, -2), 0.5, GREY_300),
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
]))
story.append(meta_t)
story.append(Spacer(1, 18))

story.append(Paragraph(
    "<b>Abstract & Discussion Context:</b> This architectural reference consolidates the design "
    "and implementation specification for the intelligent fault-detection subsystem deployed on our "
    "enterprise GPS fleet pipeline. The document details the event-driven fan-out architecture, "
    "per-ping real-time validation (GPS bounds, GSM quality, speed jumps, fuel sensor RAW values), "
    "the metadata-driven vehicle sensor capability gate, and the independent 3-scan silence watchdog "
    "for automated failure detection across enterprise fleet assets (VL149, FMC125, FMC650, iTriangle).",
    ParagraphStyle("CoverIntro", fontName="Helvetica", fontSize=8.5, leading=13.0, textColor=GREY_900, alignment=TA_JUSTIFY)))

story.append(NextPageTemplate("Body"))
story.append(PageBreak())

# ===========================================================================
# PAGE 2: TABLE OF CONTENTS & EXECUTIVE SUMMARY
# ===========================================================================
story += kicker_heading("Contents", "Table of Contents & Review Roadmap")

toc_data = [
    [Paragraph("1.", S_TOC_NUM), Paragraph("Executive Summary & System Architecture", S_TOC_TITLE), Paragraph("Page 3", S_TOC_PAGE)],
    [Paragraph("2.", S_TOC_NUM), Paragraph("End-to-End Fan-Out Architecture (Figure 1)", S_TOC_TITLE), Paragraph("Page 4", S_TOC_PAGE)],
    [Paragraph("3.", S_TOC_NUM), Paragraph("Part 1: Bad Data Detection Layer", S_TOC_TITLE), Paragraph("Page 5", S_TOC_PAGE)],
    [Paragraph("", S_TOC_NUM), Paragraph("3.1  GPS Telemetry Quality & Geographic Bounds Validation", S_TOC_TITLE), Paragraph("Page 5", S_TOC_PAGE)],
    [Paragraph("", S_TOC_NUM), Paragraph("3.2  Intelligent Fuel Validation & Vehicle Master Gate (Figure 2)", S_TOC_TITLE), Paragraph("Page 6", S_TOC_PAGE)],
    [Paragraph("4.", S_TOC_NUM), Paragraph("Part 2: Device Fault & Silence Detection Layer", S_TOC_TITLE), Paragraph("Page 7", S_TOC_PAGE)],
    [Paragraph("", S_TOC_NUM), Paragraph("4.1  Heartbeat Store (<font face='Courier'>device_status</font> Table)", S_TOC_TITLE), Paragraph("Page 7", S_TOC_PAGE)],
    [Paragraph("", S_TOC_NUM), Paragraph("4.2  Watchdog Lambda & 3-Scan Confirmation State Machine (Figure 3)", S_TOC_TITLE), Paragraph("Page 7", S_TOC_PAGE)],
    [Paragraph("", S_TOC_NUM), Paragraph("4.3  Sensor Hardware Failure vs. Transient Silence Lifecycle", S_TOC_TITLE), Paragraph("Page 8", S_TOC_PAGE)],
    [Paragraph("5.", S_TOC_NUM), Paragraph("Part 3: Implementation Steps & Deployment Sequence", S_TOC_TITLE), Paragraph("Page 9", S_TOC_PAGE)],
    [Paragraph("6.", S_TOC_NUM), Paragraph("Part 4: Ten Non-Negotiable Architecture Principles", S_TOC_TITLE), Paragraph("Page 10", S_TOC_PAGE)],
]
toc_t = Table(toc_data, colWidths=[8 * mm, 126 * mm, 22 * mm])
toc_t.setStyle(TableStyle([
    ("TOPPADDING", (0, 0), (-1, -1), 2.5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("LINEBELOW", (0, 0), (-1, -1), 0.3, GREY_150),
]))
story.append(toc_t)
story.append(Spacer(1, 14))

story.append(note_box(
    "ARCHITECTURE TEAM DISCUSSION OBJECTIVE",
    "This review aims to formalize: (1) Decoupling telemetry validation from hot database writes "
    "using parallel AWS IoT Rule fan-out; (2) Eliminating false alerts on vehicles without fuel probes "
    "via TimescaleDB <font face='Courier'>vehicle_master</font> capabilities; and (3) Guarding against false dead-device alarms "
    "using progressive 3-scan confirmation (+15 minutes threshold)."
))
story.append(PageBreak())

# ===========================================================================
# PAGE 3: SECTION 1 — SYSTEM OVERVIEW & LAYER SEPARATION
# ===========================================================================
story += kicker_heading("Section 1", "System Overview & Layer Separation")

story.append(Paragraph(
    "The fault detection platform operates across two orthogonal detection layers that run concurrently. "
    "They share a unified alerting sink (<font face='Courier'>bad_data_alerts</font> in TimescaleDB and AWS SNS) "
    "but execute under fundamentally different lifecycles and operational triggers:", S_BODY_L))
story.append(Spacer(1, 3))

layer_box_t = Table(
    [[Paragraph("<b>Layer 1 — Bad Data Detection</b>", S_TBL_BOLD),
      Paragraph("<b>Layer 2 — Device Fault / Silence Detection</b>", S_TBL_BOLD)],
     [Paragraph("<b>Question:</b> <i>Is this specific telemetry record valid?</i><br/>"
                "<b>Execution:</b> Real-time, synchronous per incoming ping.<br/>"
                "<b>Mechanisms:</b> Coordinate bounds, GSM thresholding, consecutive ping Haversine speed comparison, "
                "fuel RAW signal diagnostics, and physical slosh anomaly detection.<br/>"
                "<b>Dependency:</b> Driven directly by MQTT packet arrivals.", S_TBL),
      Paragraph("<b>Question:</b> <i>Is this physical hardware unit still alive?</i><br/>"
                "<b>Execution:</b> Decoupled, asynchronous cron every 5 minutes.<br/>"
                "<b>Mechanisms:</b> Heartbeat delta tracking on <font face='Courier'>device_status</font>, "
                "progressive 3-scan confirmation state machine (+15 minutes threshold).<br/>"
                "<b>Dependency:</b> Autonomous AWS EventBridge scheduled trigger.", S_TBL)]],
    colWidths=[CONTENT_W / 2.0, CONTENT_W / 2.0]
)
layer_box_t.setStyle(TableStyle([
    ("BOX", (0, 0), (-1, -1), 0.9, GREY_900),
    ("INNERGRID", (0, 0), (-1, -1), 0.5, GREY_300),
    ("BACKGROUND", (0, 0), (-1, 0), GREY_150),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ("LEFTPADDING", (0, 0), (-1, -1), 7),
    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
]))
story.append(layer_box_t)
story.append(Spacer(1, 6))

story.append(Paragraph("1.1  Subsystem Component Matrix", S_H2))
comp_rows = [
    ["Entry Ingestion Lambda", "Decodes hardware wire protocol, normalizes to canonical JSON, stores to hypertable, and updates heartbeat timestamp.", "MQTT Fan-out (Per ping)"],
    ["GPS Bad Data Lambda", "Validates geographic bounds (India), GSM reception, ignition bit state, and consecutive ping speed velocity.", "MQTT Fan-out (Per ping)"],
    ["Fuel Bad Data Lambda", "Queries vehicle_master for probe presence, evaluates raw analog/frequency sensor codes, and flags abnormal slosh drops.", "MQTT Fan-out (Per ping)"],
    ["Silence Watchdog Lambda", "Scans heartbeat table, advances progressive confirmation state counter (0 to 3), and declares hardware failure after 15 min.", "AWS EventBridge (5 min cron)"],
    ["bad_data_alerts Table", "Unified TimescaleDB relation capturing failure category, invalid value, root cause, device model, and detection timestamp.", "Written on anomaly failure"],
    ["AWS SNS Topic", "Distributes critical failure events in real-time to operations dashboards, Telegram/Slack webhooks, and SMS dispatchers.", "Published upon table insert"],
]
story.append(data_table(
    ["Component", "Architectural Function", "Execution Trigger"],
    comp_rows, col_widths=[105, 230, 95]))

story.append(Spacer(1, 8))
story.append(note_box(
    "CORE ARCHITECTURAL INVARIANT",
    "<b>Fail-Safe Separation of Concerns:</b> Ingestion of valid telemetry MUST NEVER be blocked "
    "or delayed by fault validation algorithms or alerting latency. By routing telemetry via AWS IoT Rule "
    "fan-out to three isolated Lambda functions in parallel, database ingestion proceeds at maximum "
    "throughput regardless of downstream SNS delivery or secondary validation processing."
))
story.append(PageBreak())

# ===========================================================================
# PAGE 4: SECTION 2 — END-TO-END FAN-OUT ARCHITECTURE
# ===========================================================================
story += kicker_heading("Section 2", "End-to-End Fan-Out Architecture")

story.append(Paragraph(
    "The telemetry pipeline uses an event-driven AWS IoT Rule fan-out pattern. When a GPS tracker "
    "publishes a message to its device topic, AWS IoT Core matches the topic filter and concurrently "
    "dispatches the complete payload to all configured target Lambdas without intermediate queuing overhead:", S_BODY_L))
story.append(Spacer(1, 4))
story.append(create_diagram_a(width=CONTENT_W, height=230))
story.append(Paragraph("Figure 1. End-to-end fan-out pipeline from device message ingestion to persistent storage and alert sinks.", S_CAPTION))

story.append(Spacer(1, 3))
story.append(Paragraph("2.1  Fan-Out Mechanics & Decoupling Benefits", S_H2))
story.append(Paragraph(
    "The SQL query configured within the AWS IoT Core Rule engine is:<br/>"
    "<font face='Courier'>&nbsp;&nbsp;SELECT *, topic(2) AS device_imei FROM 'telemetry/+/data'</font><br/>"
    "This rule simultaneously targets: (1) the <b>Entry Lambda</b> (responsible for writing to "
    "<font face='Courier'>gps_telemetry</font> and updating <font face='Courier'>device_status.last_seen</font>); "
    "(2) the <b>GPS Bad Data Lambda</b>; and (3) the <b>Fuel Bad Data Lambda</b>. "
    "Because each Lambda executes within its own isolated micro-VM, a slow query or crash in fuel validation "
    "has zero impact on high-throughput GPS ingestion.", S_BODY))

story.append(PageBreak())

# ===========================================================================
# PAGE 5: SECTION 3 — PART 1: BAD DATA DETECTION LAYER (GPS)
# ===========================================================================
story += kicker_heading("Section 3", "Part 1 — Bad Data Detection Layer")

story.append(Paragraph(
    "Bad Data Detection evaluates individual telemetry frames in real-time. It catches corrupted "
    "sensor measurements, firmware glitches, and positioning anomalies before downstream analytics consume them.", S_BODY_L))

story.append(Paragraph("3.1  GPS Bad Data Detection Specification", S_H2))
story.append(Paragraph(
    "Every incoming location record must satisfy geometric boundaries, signal integrity criteria, "
    "and kinematic physical laws:", S_BODY_L))

story.append(Paragraph("Step 1 — Geographic Boundary Validation (India Region)", S_H3))
geo_rows = [
    ["Latitude (North)", "6.7500° N", "37.1000° N", "Southern tip (Kanyakumari) to Northern border (Kashmir)"],
    ["Longitude (East)", "68.1200° E", "97.4200° E", "Western border (Gujarat) to Eastern border (Arunachal Pradesh)"],
]
story.append(data_table(["Parameter", "Minimum Bound", "Maximum Bound", "Geographic Scope"],
                        geo_rows, col_widths=[90, 75, 75, 190],
                        header_center=[1, 2], body_center_cols=[1, 2]))
story.append(Spacer(1, 3))

rule_rows = [
    ["lat == 0.0 AND lon == 0.0", "Null Island Error", "GPS receiver failed to acquire satellite lock and fell back to 0,0."],
    ["lat < 6.75 OR lat > 37.10\nOR lon < 68.12 OR lon > 97.42", "Outside Territory", "Positioning coordinates outside operational country boundary (LBS / GSM jump)."],
    ["speed_haversine > 250 km/h", "Teleportation Anomaly", "Consecutive pings require impossible physical velocity (satellite multipath reflection)."],
]
story.append(data_table(["Detection Condition", "Error Classification", "Technical Root Cause"],
                        rule_rows, col_widths=[110, 95, 225], mono_cols=[0]))
story.append(Spacer(1, 4))

story.append(Paragraph("Step 2 — GSM Cellular Signal Validation", S_H3))
gsm_rows = [
    ["1 to 5 (or CSQ 6–31)", "VALID", "Normal cellular link quality. Record accepted."],
    ["0 or negative (CSQ 0–5)", "BAD DATA", "Zero / marginal reception. Suspected jammer, tunnel, or antenna disconnect."],
    ["> 5 (or CSQ 99)", "BAD DATA", "Modem error code (99 = not known or not detectable). Hardware fault."],
    ["NULL / Missing", "BAD DATA", "Modem failed to populate field in payload string. Protocol decode error."],
]
story.append(data_table(["GSM Signal Value", "Status", "Evaluation & Engineering Meaning"],
                        gsm_rows, col_widths=[105, 65, 260], header_center=[1], body_center_cols=[1]))
story.append(Spacer(1, 4))

story.append(Paragraph("Step 3 — Ignition State Bit Validation", S_H3))
story.append(Paragraph(
    "Condition: <font face='Courier'>IF ignition NOT IN (0, 1) OR ignition IS NULL</font> → <b>FLAG BAD DATA</b>. "
    "Only binary digital inputs (<font face='Courier'>0 = OFF</font>, <font face='Courier'>1 = ON</font>) "
    "are permissible. Floating or undefined values indicate harness wiring failure.", S_BODY_L))
story.append(Spacer(1, 3))

story.append(Paragraph("Step 4 — Consecutive Ping Haversine Speed Jump Verification", S_H3))
story.append(Paragraph(
    "Speed reported by device firmware cannot be validated in isolation. The Lambda fetches the "
    "immediately preceding ping from TimescaleDB and computes the great-circle speed:", S_BODY_L))
story.append(note_box(
    "HAVERSINE KINEMATIC INTEGRITY RULE",
    "Let <font face='Courier'>D = Haversine_Distance(lat1, lon1, lat2, lon2)</font> and "
    "<font face='Courier'>ΔT = Time_Difference(t1, t2)</font>.<br/>"
    "<b>Rule:</b> <font face='Courier'>IF (D / ΔT) &gt; 250 km/h THEN FLAG BAD DATA (GPS_JUMP)</font>.<br/>"
    "This calculation filters out momentary satellite constellation shifts and cellular tower fallback hops."
))
story.append(PageBreak())

# ===========================================================================
# PAGE 6: SECTION 3.2 — INTELLIGENT FUEL SENSOR VALIDATION
# ===========================================================================
story += kicker_heading("Section 3.2", "Intelligent Fuel Bad Data Detection")

story.append(Paragraph(
    "<b>Metadata-Driven Validation Gate:</b> A primary source of false alerts in commercial fleet systems "
    "is running fuel diagnostics against vehicles that do not physically possess fuel sensors. "
    "The Fuel Bad Data Lambda first queries the <font face='Courier'>vehicle_master</font> catalog in TimescaleDB "
    "to verify sensor fitment before executing any mathematical validation rules:", S_BODY_L))
story.append(Spacer(1, 4))
story.append(create_diagram_c(width=CONTENT_W, height=145))
story.append(Paragraph("Figure 2. vehicle_master capability lookup decision gate executed prior to fuel validation.", S_CAPTION))

story.append(Spacer(1, 2))
story.append(Paragraph("Vehicle Master Relation Schema (<font face='Courier'>vehicle_master</font>)", S_H3))
vm_rows = [
    ["imei", "TEXT (PRIMARY KEY)", "Unique international hardware modem identifier."],
    ["vehicle_name", "TEXT", "License plate or commercial asset registration number."],
    ["vehicle_type", "TEXT", "Asset classification: Heavy Truck, Reefer, Tanker, Light Van."],
    ["has_fuel_sensor", "BOOLEAN", "TRUE = Capacitive/Ultrasonic LLS fuel probe installed."],
    ["fuel_sensor_count", "INT (1 to 5)", "Number of calibrated tanks/sensors connected via RS485/Analog."],
    ["has_temp_sensor", "BOOLEAN", "TRUE = Dallas 1-Wire temperature sensor equipped for cold chain."],
    ["has_tpms", "BOOLEAN", "TRUE = BLE or RF tire pressure monitoring system installed."],
]
story.append(data_table(["Column Name", "Data Type", "Architectural Purpose & Semantics"],
                        vm_rows, col_widths=[95, 100, 235], mono_cols=[0]))
story.append(Spacer(1, 4))

story.append(Paragraph("Fuel Sensor RAW Value Failure Modes & Rules", S_H3))
fuel_rows = [
    ["RAW = -4", "Cable Cut / Disconnected", "Flag Bad Data + Raise Hardware Alert"],
    ["RAW = -128", "Temperature Probe Disconnected", "Flag Bad Data + Raise Cold Chain Alert"],
    ["RAW = 0", "Dead Sensor / Zero Voltage", "Flag Bad Data (Defective calibration)"],
    ["RAW 1 to 4094", "Valid Linear Sensor Measurement", "ACCEPT (Safe for volumetric calibration)"],
    ["RAW = 4095", "Short Circuit / Diagnostic Fault", "Flag Bad Data + Raise Hardware Alert"],
    ["RAW > 4095", "Register Overflow / Corrupted Bytes", "Flag Bad Data (Bus transmission error)"],
]
story.append(data_table(["Sensor RAW Code", "Failure Mode / Physical Condition", "Action & Alert Protocol"],
                        fuel_rows, col_widths=[90, 185, 155], header_center=[0], body_center_cols=[0]))
story.append(Spacer(1, 4))

story.append(note_box(
    "SLOSH ANOMALY DETECTION RULE",
    "<b>Rule:</b> <font face='Courier'>IF (Fuel_Drop &gt; 30% BETWEEN CONSECUTIVE PINGS) THEN FLAG BAD DATA (SLOSH_ANOMALY)</font>.<br/>"
    "<b>Physical Rationale:</b> Liquid diesel cannot be physically consumed at a rate exceeding 30% within "
    "a single 10–30 second ping interval. Sudden drops indicate float failure, wiring intermittent contact, "
    "or violent road vibration — NOT a bona fide fuel theft event."
))
story.append(PageBreak())


# ===========================================================================
# PAGE 8: SECTION 4 — PART 2: DEVICE FAULT & SILENCE DETECTION
# ===========================================================================
story += kicker_heading("Section 4", "Part 2 — Device Fault & Silence Detection")

story.append(Paragraph(
    "Device Fault Detection operates independently from Bad Data Detection. While Bad Data checks "
    "the integrity of active messages, Fault Detection monitors for the <b>cessation of communication</b>. "
    "A device is only declared DEAD after failing across three consecutive confirmation scans (15 minutes total).", S_BODY_L))

story.append(Paragraph("4.1  Heartbeat State Store (<font face='Courier'>device_status</font> Table)", S_H2))
story.append(Paragraph(
    "On every incoming telemetry ping, the Entry Lambda executes a fast atomic upsert into "
    "the heartbeat table. This table maintains exactly one record per registered device:", S_BODY_L))
hb_rows = [
    ["imei", "TEXT (PK)", "Entry Lambda (On every ping)", "Unique device hardware identifier."],
    ["last_seen", "TIMESTAMPTZ", "Entry Lambda (On every ping)", "UTC timestamp of the most recent valid packet."],
    ["ignition_status", "TEXT (ON/OFF)", "Entry Lambda (On every ping)", "Latest reported vehicle ignition state."],
    ["fault_scan_count", "INT (0 to 3)", "Watchdog Lambda (Scheduled)", "Consecutive scan silence failure counter."],
    ["fault_status", "TEXT (Enum)", "Watchdog Lambda (Scheduled)", "'HEALTHY', 'SUSPECTED_FAULT', 'FAULT_CONFIRMING', 'DEVICE_DEAD'."],
]
story.append(data_table(["Column Name", "Data Type", "Updating Subsystem", "Description & State"],
                        hb_rows, col_widths=[85, 95, 120, 130], mono_cols=[0]))
story.append(Spacer(1, 4))

story.append(Paragraph("4.2  Watchdog Lambda — Three-Scan Confirmation State Machine", S_H2))
story.append(Spacer(1, 4))
story.append(create_diagram_b(width=CONTENT_W, height=155))
story.append(Paragraph("Figure 3. Watchdog 3-scan confirmation state machine evaluated autonomously per device.", S_CAPTION))

story.append(Spacer(1, 2))
scan_rows = [
    ["Scan 1", "+5 Minutes Silence", "SUSPECTED_FAULT", "fault_scan_count = 1. Internal state update only. NO ALERT."],
    ["Scan 2", "+10 Minutes Silence", "FAULT_CONFIRMING", "fault_scan_count = 2. Internal state update only. NO ALERT."],
    ["Scan 3", "+15 Minutes Silence", "DEVICE_DEAD", "fault_scan_count = 3. RAISE CRITICAL ALERT via AWS SNS & insert to bad_data_alerts."],
    ["Any Scan", "Incoming Ping Received", "HEALTHY", "Ping received within window. Reset fault_scan_count = 0. Clear active alarms."],
]
story.append(data_table(["Execution", "Silence Duration", "New State Assigned", "Operational Action & Alerting Protocol"],
                        scan_rows, col_widths=[55, 95, 100, 180], header_center=[0]))
story.append(PageBreak())

# ===========================================================================
# PAGE 9: SECTION 4.3 — SENSOR FAULT LIFECYCLE & NOISE SUPPRESSION
# ===========================================================================
story += kicker_heading("Section 4.3", "Sensor Hardware Failure vs. Transient Noise")

story.append(Paragraph(
    "<b>Sub-Component Sensor Failure vs. Vehicle Silence:</b> Just as a full device silence requires "
    "a progressive 3-scan confirmation, individual sensor hardware failures (such as severed LLS probe "
    "cables or disconnected 1-Wire temperature sensors) also adhere to multi-scan confirmation before "
    "declaring a permanent hardware breakdown:", S_BODY_L))
story.append(Spacer(1, 4))

sensor_matrix = [
    ["Persistent Cut Cable\n(RAW = -4 throughout)", "Suspected Cable Cut\n(Count = 1)", "Confirming Cable Cut\n(Count = 2)", "SENSOR DEAD ALERT\n(Raise Maintenance Ticket)"],
    ["Transient Disconnect\n(-4 then Valid Reading)", "Suspected Cable Cut\n(Count = 1)", "RECOVERED TO HEALTHY\n(Clear Counter = 0)", "Normal Operations\n(No Alert Dispatched)"],
    ["Short Circuit Fault\n(RAW = 4095 throughout)", "Suspected Short Circuit\n(Count = 1)", "Confirming Short Circuit\n(Count = 2)", "HARDWARE FAULT ALERT\n(Probe Shorted Out)"],
    ["Healthy Operational Band\n(RAW 1-4094 throughout)", "HEALTHY (Normal)", "HEALTHY (Normal)", "Continuous Telemetry Store\n(Zero Interruption)"],
]
story.append(data_table(["Failure Signature", "Scan 1 (+5 min)", "Scan 2 (+10 min)", "Final Resolution (Scan 3)"],
                        sensor_matrix, col_widths=[110, 100, 105, 115], header_center=[1, 2]))
story.append(Spacer(1, 8))

story.append(note_box(
    "FLEET INDEPENDENCE & ISOLATION GUARANTEE",
    "<b>State Independence:</b> Every device and sensor maintains an isolated row within <font face='Courier'>device_status</font>. "
    "If vehicle A recovers from silence while vehicle B remains silent, vehicle A's counter resets to 0 with zero "
    "cross-talk or impact on vehicle B's pending dead-device confirmation. The state machine is strictly per-entity."
))
story.append(Spacer(1, 8))

story.append(Paragraph("Unified Alert Schema (<font face='Courier'>bad_data_alerts</font>)", S_H3))
alert_rows = [
    ["alert_id", "BIGSERIAL (PK)", "Unique sequential alert event identifier."],
    ["device_id", "TEXT", "Hardware IMEI associated with the failure event."],
    ["device_model", "TEXT", "Device protocol / hardware model ('VL149', 'FMC125', etc.)."],
    ["alert_type", "TEXT", "'GPS_BOUNDS', 'SPEED_JUMP', 'FUEL_DISCONNECT', 'DEVICE_DEAD'."],
    ["bad_field", "TEXT", "Specific field failing validation ('latitude', 'fuel_raw', 'heartbeat')."],
    ["bad_value", "TEXT", "Recorded value triggering violation ('0.0', '-4', '99', '284 km/h')."],
    ["reason", "TEXT", "Detailed engineering root cause explanation for auditing."],
    ["detected_at", "TIMESTAMPTZ", "UTC timestamp when the anomaly was verified and recorded."],
]
story.append(data_table(["Column Name", "Data Type", "Architectural Semantics"],
                        alert_rows, col_widths=[95, 105, 230], mono_cols=[0]))
story.append(PageBreak())

# ===========================================================================
# PAGE 10: SECTION 5 — IMPLEMENTATION STEPS & DEPLOYMENT ROADMAP
# ===========================================================================
story += kicker_heading("Section 5", "Part 3 — Step-by-Step Implementation Guide")

story.append(Paragraph(
    "The fault detection platform is deployed via an eight-stage engineering sequence. "
    "Each stage has concrete acceptance criteria to ensure zero disruption to live telemetry ingestion:", S_BODY_L))
story.append(Spacer(1, 3))

steps = [
    ("Stage 1", "TimescaleDB Schema Provisioning",
     "Execute DDL migrations to create <font face='Courier'>device_status</font>, "
     "<font face='Courier'>vehicle_master</font>, and <font face='Courier'>bad_data_alerts</font>. "
     "Populate vehicle capabilities (<font face='Courier'>has_fuel_sensor</font>, probe counts) from ERP inventory."),
    ("Stage 2", "Entry Lambda Enhancement & Heartbeat Instrumentation",
     "Update the active Entry Ingestion Lambda (<font face='Courier'>gt06_lambda.py</font> / FMC service) to execute "
     "an upsert into <font face='Courier'>device_status.last_seen</font> on every valid ping. Runtime: Python 3.12."),
    ("Stage 3", "Deploy GPS Bad Data Lambda Package",
     "Deploy <font face='Courier'>GPS_BadData_Detection_Lambda.zip</font> with psycopg2 binary layer. "
     "Configure environment variables: <font face='Courier'>DB_HOST</font>, <font face='Courier'>DB_NAME</font>, "
     "<font face='Courier'>DB_USER</font>, <font face='Courier'>WRITER_SECRET_ID</font>."),
    ("Stage 4", "Deploy Fuel Bad Data Lambda Package",
     "Deploy <font face='Courier'>Fuel_BadData_Detection_Lambda.zip</font> incorporating the "
     "<font face='Courier'>vehicle_master</font> capability check and RAW diagnostic thresholds. Configure identical DB credentials."),
    ("Stage 5", "Configure AWS IoT Core Rule Fan-Out Actions",
     "In AWS IoT Core, add 3 concurrent Rule Actions targeting: (1) Entry Lambda, (2) GPS Bad Data Lambda, "
     "(3) Fuel Bad Data Lambda. Verify simultaneous parallel dispatch across all incoming telemetry pings."),
    ("Stage 6", "Deploy Silence Watchdog Lambda & AWS EventBridge Cron",
     "Deploy <font face='Courier'>watchdog_lambda.py</font>. Create an AWS EventBridge Schedule with fixed rate "
     "<font face='Courier'>rate(5 minutes)</font> granting execution rights to query <font face='Courier'>device_status</font>."),
    ("Stage 7", "AWS SNS Topic & Notification Subscriptions",
     "Create dedicated SNS Topic <font face='Courier'>arn:aws:sns:*:*:fleet-telemetry-fault-alerts</font>. "
     "Subscribe operational Webhooks, Slack channels, and SMS endpoints. Grant Lambda publishing permissions."),
    ("Stage 8", "End-to-End Fleet Verification & Telemetry Audit",
     "Simulate Null Island (0,0), disconnected fuel probes (-4), and 15-minute simulated silence. "
     "Verify that alerts populate in <font face='Courier'>bad_data_alerts</font> and SNS dispatches without error."),
]

step_table_data = []
for num, title, desc in steps:
    step_table_data.append([
        Paragraph(num, ParagraphStyle("snum", fontName="Helvetica-Bold", fontSize=7.8, textColor=WHITE, alignment=TA_CENTER)),
        Paragraph(f"<b>{title}</b><br/><font size=7.4 color='#333333'>{desc}</font>",
                  ParagraphStyle("sdesc", fontName="Helvetica", fontSize=8.0, leading=11.0, textColor=INK))
    ])

step_t = Table(step_table_data, colWidths=[18 * mm, 152 * mm])
step_style = [
    ("BACKGROUND", (0, 0), (0, -1), GREY_900),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 3.5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ("LEFTPADDING", (1, 0), (1, -1), 7),
    ("LEFTPADDING", (0, 0), (0, -1), 0),
    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ("BOX", (0, 0), (-1, -1), 0.75, GREY_300),
]
for i in range(len(step_table_data)):
    if i % 2 == 1:
        step_style.append(("BACKGROUND", (1, i), (1, i), GREY_100))
    step_style.append(("LINEBELOW", (0, i), (-1, i), 0.4, GREY_300))
step_t.setStyle(TableStyle(step_style))
story.append(step_t)
story.append(PageBreak())

# ===========================================================================
# PAGE 11: SECTION 6 — TEN CORE ARCHITECTURE PRINCIPLES
# ===========================================================================
story += kicker_heading("Section 6", "Part 4 — Ten Core Architecture Principles")

story.append(Paragraph(
    "These ten architectural principles serve as non-negotiable engineering mandates for maintaining "
    "high reliability, zero false-alert noise, and horizontal scalability across our fleet platform:", S_BODY_L))
story.append(Spacer(1, 3))

principles = [
    ("01", "Three-Scan Silence Confirmation",
     "Never declare a device dead from a single missed ping. Always require three consecutive 5-minute silence scans (+15 min threshold) before raising an operational dead-device alert."),
    ("02", "Metadata Capability Checking Before Validation",
     "Query vehicle_master before executing fuel diagnostics. If a vehicle has no fuel sensor installed, immediately bypass validation with zero false alerts."),
    ("03", "RAW Code Range Isolation",
     "Never use fuel RAW values outside the calibrated 1–4094 range for volumetric calculations. Out-of-bounds codes represent diagnostic fault signatures, not fuel volume."),
    ("04", "Independent Lifecycle Decoupling",
     "Bad Data Detection runs synchronously per-record; Device Silence Watchdog runs asynchronously every 5 minutes. Neither subsystem depends on the execution state of the other."),
    ("05", "Independent State Tracking per Device",
     "Every device maintains its own isolated fault_scan_count. A recovery event on one vehicle must never alter, reset, or interfere with another vehicle's pending failure counter."),
    ("06", "Instantaneous Recovery & Counter Reset",
     "The moment a device transmits a valid telemetry record, immediately reset its fault_scan_count to 0 and clear any active warning state."),
    ("07", "Kinematic Speed Verification",
     "Never validate reported speed in isolation. Always compute great-circle Haversine velocity between consecutive pings to detect GPS multipath jumps (> 250 km/h)."),
    ("08", "Canonical Schema Adapter Decoupling",
     "Normalize all incoming tracker wire formats (VL149, FMC125, iTriangle) into a uniform Canonical Telemetry Contract at the entry boundary. Validation Lambdas remain protocol-agnostic."),
    ("09", "Comprehensive Root-Cause Auditing",
     "Record the explicit root-cause reason, failing attribute, and raw offending value for every anomaly within bad_data_alerts to support engineering diagnostics and field service audits."),
    ("10", "Asynchronous Alert Path Separation",
     "Separate alerting dispatch (AWS SNS) from core telemetry storage (TimescaleDB). An alert publishing failure must NEVER delay or abort high-throughput database writes."),
]

prin_data = []
for num, title, desc in principles:
    prin_data.append([
        Paragraph(num, S_PRINCIPLE_NUM),
        Paragraph(f"<b>{title}:</b> {desc}", S_PRINCIPLE_TXT)
    ])

prin_t = Table(prin_data, colWidths=[11 * mm, 159 * mm])
prin_style = [
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 3.5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ("LEFTPADDING", (1, 0), (1, -1), 6),
    ("LEFTPADDING", (0, 0), (0, -1), 0),
    ("LINEBELOW", (0, 0), (-1, -2), 0.4, GREY_300),
]
prin_t.setStyle(TableStyle(prin_style))
story.append(prin_t)
story.append(Spacer(1, 10))

story.append(rule())
story.append(Paragraph(
    "<b>Architecture Review Conclusion:</b> This technical specification represents the baseline "
    "for engineering sign-off. Changes to database contracts or threshold constants must be submitted via "
    "Architecture Decision Record (ADR) prior to production deployment.", S_SMALL))

# ---------------------------------------------------------------------------
# BUILD DOCUMENT
# ---------------------------------------------------------------------------
doc.build(story, canvasmaker=ArchitectureCanvas)
print(f"Professional Architecture PDF built successfully: {PDF_OUT_PATH}")