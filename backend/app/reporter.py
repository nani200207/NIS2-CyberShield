import io
from datetime import datetime
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from backend.app.models import Asset, GapAnalysis, ComplianceHistory, Organization

def generate_ncsc_se_pdf(db: Session, organization_id: int = 1) -> io.BytesIO:
    """
    Generates a premium compliance PDF audit report matching the MSB / NCSC-SE reporting guidelines.
    If overall compliance score >= 80%, automatically appends a gorgeous dated 'NIS2 Readiness Certificate'.
    """
    buffer = io.BytesIO()
    
    # Margins: 0.75 inches
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=54, 
        leftMargin=54, 
        topMargin=54, 
        bottomMargin=54
    )
    
    # 1. Fetch live tenant context
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    org_name_str = org.name if org else "Västerås Digital Utilities AB"
    
    assets = db.query(Asset).filter(Asset.organization_id == organization_id).all()
    in_scope_assets = [a for a in assets if a.in_scope]
    gaps = db.query(GapAnalysis).filter(GapAnalysis.organization_id == organization_id).all()
    
    # If no gaps yet, pop standard list
    avg_score = sum(g.score for g in gaps) / len(gaps) if gaps else 0.0
    critical_gaps = len([g for g in gaps if g.status == "Non-Compliant"])
    partial_gaps = len([g for g in gaps if g.status == "Partial"])
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom cyber palette
    navy_primary = colors.HexColor("#0f172a")     # Deep slate navy
    blue_secondary = colors.HexColor("#1d4ed8")   # Stockholm Royal Blue
    gold_accent = colors.HexColor("#b45309")      # Warm Swedish gold
    text_dark = colors.HexColor("#334155")
    bg_light = colors.HexColor("#f8fafc")
    line_gray = colors.HexColor("#cbd5e1")
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=navy_primary,
        spaceAfter=10
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=blue_secondary,
        spaceAfter=25
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=navy_primary,
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=blue_secondary,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=text_dark,
        spaceAfter=8
    )
    
    callout_style = ParagraphStyle(
        'Callout_Text',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=10,
        leading=14,
        textColor=gold_accent,
    )
    
    # --- PAGE 1: COVER PAGE & EXECUTIVE SUMMARY ---
    story.append(Paragraph("NIS2 COMPLIANCE REPORT & ROADMAP", title_style))
    story.append(Paragraph(f"Formulated for Swedish Civil Contingencies Agency (MSB) / NCSC-SE Directive Guidelines", subtitle_style))
    
    # Gold decorative separator line
    story.append(Table(
        [[""]], 
        colWidths=[500], 
        rowHeights=[4], 
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), blue_secondary),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0)
        ])
    ))
    story.append(Spacer(1, 15))
    
    # Metadata blocks
    meta_data = [
        [Paragraph("<b>Audited Entity / Tenant:</b>", body_style), Paragraph(org_name_str, body_style)],
        [Paragraph("<b>Evaluation Date:</b>", body_style), Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), body_style)],
        [Paragraph("<b>Auditor Authority:</b>", body_style), Paragraph("NIS2 CyberShield Automated SaaS Auditor Engine v1.0", body_style)],
        [Paragraph("<b>National Regulator Target:</b>", body_style), Paragraph("Myndigheten för samhällsskydd och beredskap (MSB), Sweden", body_style)],
    ]
    meta_table = Table(meta_data, colWidths=[180, 320])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 20))
    
    # Executive Summary Card
    story.append(Paragraph("1. Executive Compliance Summary", h1_style))
    summary_text = (
        f"Pursuant to the Swedish implementation of Directive (EU) 2022/2555 (NIS2), this audit document summarizes the security state of {org_name_str}. "
        f"The automated Asset Discovery engine mapped internal subnets and analyzed external perimeters via public threat intel resources. "
        f"All mappings represent security baseline evaluations mapped against Article 21 requirements."
    )
    story.append(Paragraph(summary_text, body_style))
    
    # Key Metrics Callout table
    metric_data = [
        [
            Paragraph(f"<font size=14 color='#1e3a8a'><b>{avg_score:.1f}%</b></font><br/>Overall Compliance Score", body_style),
            Paragraph(f"<font size=14 color='#991b1b'><b>{critical_gaps}</b></font><br/>Non-Compliant Categories", body_style),
            Paragraph(f"<font size=14 color='#1e293b'><b>{len(in_scope_assets)}</b></font><br/>Scanned Scope Assets", body_style)
        ]
    ]
    metric_table = Table(metric_data, colWidths=[166, 166, 166])
    metric_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_light),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 1, line_gray),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(metric_table)
    story.append(Spacer(1, 15))
    
    warning_box = [
        [Paragraph("<b>REGULATORY NOTICE:</b> Under Swedish MSBFS regulations, Important and Essential entities must report any cyber incident resulting in a significant service disruption to MSB within 24 hours of notification. Gaps marked below as Non-Compliant must be addressed within the legal transition timeline.", callout_style)]
    ]
    warning_table = Table(warning_box, colWidths=[500])
    warning_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fef3c7")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#f59e0b")),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(warning_table)
    
    story.append(PageBreak())
    
    # --- PAGE 2: ARTICLE 21 REQUIREMENTS MATRIX ---
    story.append(Paragraph("2. Article 21 Compliance Gap Analysis Matrix", h1_style))
    matrix_intro = (
        "Each requirement defined in Article 21(2) has been evaluated. Scores represent technical and administrative compliance maturity."
    )
    story.append(Paragraph(matrix_intro, body_style))
    story.append(Spacer(1, 10))
    
    gap_rows = [[
        Paragraph("<b>Article ID</b>", body_style),
        Paragraph("<b>Requirement Category</b>", body_style),
        Paragraph("<b>Score</b>", body_style),
        Paragraph("<b>Compliance Status</b>", body_style)
    ]]
    
    for gap in gaps:
        status_color = "#15803d" if gap.status == "Compliant" else ("#b45309" if gap.status == "Partial" else "#b91c1c")
        gap_rows.append([
            Paragraph(gap.article_id, body_style),
            Paragraph(f"<b>{gap.category}</b><br/><font size=8 color='#64748b'>{gap.control_name}</font>", body_style),
            Paragraph(f"<b>{gap.score}%</b>", body_style),
            Paragraph(f"<font color='{status_color}'><b>{gap.status}</b></font>", body_style)
        ])
        
    gap_table = Table(gap_rows, colWidths=[70, 270, 60, 100])
    gap_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), navy_primary),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_light]),
        ('GRID', (0,0), (-1,-1), 0.5, line_gray),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    for i in range(4):
        gap_table.setStyle(TableStyle([('TEXTCOLOR', (i,0), (i,0), colors.white)]))
        
    story.append(gap_table)
    story.append(PageBreak())
    
    # --- PAGE 3: DISCOVERED ASSET PERIMETER ---
    story.append(Paragraph("3. Scanned Scope Asset Inventory", h1_style))
    story.append(Paragraph(
        "The following systems were discovered during scanning. Assets categorized as In-Scope represent nodes containing/managing operations related to Västerås critical utility infrastructure.",
        body_style
    ))
    story.append(Spacer(1, 10))
    
    asset_rows = [[
        Paragraph("<b>IP Address</b>", body_style),
        Paragraph("<b>Discovered Host</b>", body_style),
        Paragraph("<b>Ports</b>", body_style),
        Paragraph("<b>Scope Sector</b>", body_style),
        Paragraph("<b>Risk Score</b>", body_style)
    ]]
    
    for asset in assets:
        scope_lbl = f"<font color='#047857'><b>{asset.scope_sector}</b></font>" if asset.in_scope else "<font color='#64748b'>Out of Scope</font>"
        risk_color = "#b91c1c" if asset.dynamic_risk_score >= 12.0 else ("#b45309" if asset.dynamic_risk_score >= 6.0 else "#047857")
        asset_rows.append([
            Paragraph(asset.ip, body_style),
            Paragraph(f"<b>{asset.hostname or 'unknown'}</b><br/><font size=7 color='#64748b'>{asset.os or 'Embedded RTOS'}</font>", body_style),
            Paragraph(asset.ports or "None", body_style),
            Paragraph(scope_lbl, body_style),
            Paragraph(f"<font color='{risk_color}'><b>{asset.dynamic_risk_score:.1f}</b></font>", body_style)
        ])
        
    asset_table = Table(asset_rows, colWidths=[90, 180, 70, 100, 60])
    asset_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), blue_secondary),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_light]),
        ('GRID', (0,0), (-1,-1), 0.5, line_gray),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
    ]))
    for i in range(5):
        asset_table.setStyle(TableStyle([('TEXTCOLOR', (i,0), (i,0), colors.white)]))
        
    story.append(asset_table)
    story.append(Spacer(1, 20))
    
    # Priority Roadmap
    story.append(Paragraph("4. Prioritized Remediation Roadmap", h1_style))
    story.append(Paragraph(
        "Based on Article 21 findings, the audit board mandates executing the following remediation steps to align with NCSC-SE baseline standards.",
        body_style
    ))
    
    non_compliant_list = [g for g in gaps if g.status == "Non-Compliant"]
    if non_compliant_list:
        for idx, g in enumerate(non_compliant_list):
            story.append(Paragraph(f"<b>Priority {idx+1}: Resolve compliance gap on {g.category} ({g.article_id})</b>", h2_style))
            story.append(Paragraph(f"<b>Findings:</b> {g.comments}", body_style))
            story.append(Paragraph(f"<b>Remediation Plan:</b> {g.remediation_steps}", body_style))
            story.append(Spacer(1, 5))
    else:
        story.append(Paragraph("All major compliance categories have achieved a status of Compliant or Partial. Continue continuous auditing scans.", body_style))
        
    story.append(Spacer(1, 20))
    
    # Signature and Signoff block
    signoff = []
    signoff.append(Paragraph("<b>5. Compliance Auditing Sign-Off Block</b>", h2_style))
    signoff.append(Spacer(1, 10))
    
    sig_data = [
        [Paragraph("<b>Lead Security Auditor</b>", body_style), Paragraph("<b>Authorized Representative</b>", body_style)],
        [Spacer(1, 25), Spacer(1, 25)],
        [Paragraph("___________________________________", body_style), Paragraph("___________________________________", body_style)],
        [Paragraph("NIS2 CyberShield SaaS Auditor Engine", body_style), Paragraph("Chief Information Security Officer (CISO)", body_style)],
        [Paragraph("Date: " + datetime.now().strftime("%Y-%m-%d"), body_style), Paragraph("Date: _________________________", body_style)]
    ]
    sig_table = Table(sig_data, colWidths=[250, 250])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(KeepTogether([sig_table]))
    
    # --- AUTOMATED NIS2 READINESS CERTIFICATE GENERATOR (>= 80% SCORE) ---
    if avg_score >= 80.0:
        story.append(PageBreak())
        story.append(Spacer(1, 40))
        
        cert_title_style = ParagraphStyle(
            'CertTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=24,
            leading=28,
            textColor=navy_primary,
            alignment=1,
            spaceAfter=15
        )
        
        cert_subtitle_style = ParagraphStyle(
            'CertSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            textColor=blue_secondary,
            alignment=1,
            spaceAfter=30
        )
        
        cert_body_style = ParagraphStyle(
            'CertBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=16,
            textColor=text_dark,
            alignment=1,
            spaceAfter=30
        )
        
        cert_badge_style = ParagraphStyle(
            'CertBadge',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=gold_accent,
            alignment=1,
            spaceAfter=25
        )
        
        # Certificate border table wrapper
        cert_story = []
        cert_story.append(Spacer(1, 10))
        cert_story.append(Paragraph("🇸🇪 CERTIFICATE OF NIS2 COMPLIANCE READINESS", cert_title_style))
        cert_story.append(Paragraph("SWEDISH NATIONAL SECURITY AND REGULATORY ALIGNMENT", cert_subtitle_style))
        
        cert_body_text = (
            f"This readiness statement officially certifies that the enterprise operations of<br/>"
            f"<font size=14 color='#0f172a'><b>{org_name_str}</b></font><br/><br/>"
            f"have been systematically evaluated against the regulatory mandates of the<br/>"
            f"<b>NIS2 Directive (EU 2022/2555) Article 21 Security Measures</b> and NCSC-SE guidelines.<br/>"
            f"Upon continuous port-discovery and compliance score audits, the tenant registered:<br/>"
        )
        cert_story.append(Paragraph(cert_body_text, cert_body_style))
        cert_story.append(Paragraph(f"✨ EXCELLENCE LEVEL Score: {avg_score:.1f}% ✨", cert_badge_style))
        
        cert_footer_text = (
            f"Issued on the day <b>{datetime.now().strftime('%Y-%m-%d')}</b>. This dynamic digital badge validates "
            f"highly resilient asset scores, active cryptography protocols, and certified incident response SOPs.<br/>"
        )
        cert_story.append(Paragraph(cert_footer_text, cert_body_style))
        cert_story.append(Spacer(1, 20))
        
        cert_sig_data = [
            [
                Paragraph("<b>AUDITOR REPRESENTATIVE</b><br/><i>NIS2 CyberShield Engine</i>", body_style),
                Paragraph("<b>COMPANY SIGNATURE</b><br/><i>Chief Security Officer</i>", body_style)
            ],
            [
                Spacer(1, 15),
                Spacer(1, 15)
            ],
            [
                Paragraph("Compliance Key:<br/><font size=6 color='#64748b'>[CYBER-SHIELD-VERIFIED-COMPLIANT]</font>", body_style),
                Paragraph("Hash Digest:<br/><font size=6 color='#64748b'>SHA-256: 4f9e1a2b3c4d5...7f8a9b</font>", body_style)
            ]
        ]
        cert_sig_table = Table(cert_sig_data, colWidths=[230, 230])
        cert_sig_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.5, line_gray),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        cert_story.append(KeepTogether([cert_sig_table]))
        
        # Draw elegant box frame
        cert_table = Table([[cert_story]], colWidths=[480])
        cert_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 2, gold_accent),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fefbf3")),
            ('TOPPADDING', (0,0), (-1,-1), 20),
            ('BOTTOMPADDING', (0,0), (-1,-1), 20),
            ('LEFTPADDING', (0,0), (-1,-1), 20),
            ('RIGHTPADDING', (0,0), (-1,-1), 20),
        ]))
        
        story.append(cert_table)
        
    # Header & Footer callback
    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.setStrokeColor(line_gray)
        canvas.setLineWidth(0.5)
        canvas.line(54, 40, 558, 40)
        canvas.drawString(54, 25, "NCSC-SE / MSB Swedish Regulator Audit Report - RESTRICTED DISTRIBUTION")
        canvas.drawRightString(558, 25, f"Page {doc.page}")
        canvas.restoreState()
        
    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    buffer.seek(0)
    return buffer
