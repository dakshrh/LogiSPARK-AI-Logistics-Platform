import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from datetime import datetime

def generate_emergency_pdf(data: dict) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#dc2626'), spaceAfter=14
    )
    heading_style = ParagraphStyle(
        'CustomHeading', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#1e3a8a'), spaceAfter=10, spaceBefore=16
    )
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    normal_style.spaceAfter = 6
    
    elements = []
    
    # Header
    elements.append(Paragraph(f"<b>LogiSPARK</b> - Emergency Recovery Plan", title_style))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    elements.append(Spacer(1, 10))
    
    # Shipment Info
    elements.append(Paragraph("<b>1. Shipment Information</b>", heading_style))
    info_data = [
        ["Transport Type", data.get("transport_type", "N/A"), "Severity", data.get("severity_label", "N/A")],
        ["Origin", data.get("origin", "N/A"), "Destination", data.get("destination", "N/A")],
        ["Cargo Value (INR)", f"{data.get('cargo_value', 0):,}", "Current Delay", f"{data.get('current_delay_hrs', 0)} hrs"]
    ]
    t_info = Table(info_data, colWidths=[120, 140, 120, 140])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f1f5f9')),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(t_info)
    
    # Action Plan
    elements.append(Paragraph("<b>2. AI Action Plan</b>", heading_style))
    elements.append(Paragraph(f"<b>Recommended Action:</b> {data.get('recommended_action', '')}", normal_style))
    elements.append(Paragraph(f"{data.get('action_description', '')}", normal_style))
    elements.append(Paragraph(f"<b>AI Narrative:</b> {data.get('ai_narrative', '')}", normal_style))
    
    # Financial Impact
    elements.append(Paragraph("<b>3. Financial Impact Analysis</b>", heading_style))
    fin_data = [
        ["Estimated Loss (No Action)", f"Rs. {data.get('estimated_loss', 0):,}"],
        ["Implementation Cost", f"Rs. {data.get('implementation_cost', 0):,}"],
        ["Expected Savings", f"Rs. {data.get('estimated_savings', 0):,}"],
        ["Net Benefit", f"Rs. {data.get('net_benefit', 0):,}"]
    ]
    t_fin = Table(fin_data, colWidths=[200, 200])
    t_fin.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f1f5f9')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (1,2), (1,3), colors.HexColor('#10b981')), # Green for savings
        ('TEXTCOLOR', (1,0), (1,0), colors.HexColor('#ef4444')), # Red for loss
    ]))
    elements.append(t_fin)
    
    # Alternate Carriers
    elements.append(Paragraph("<b>4. Alternate Carriers</b>", heading_style))
    carriers = data.get("carrier_suggestions", [])
    if carriers:
        c_data = [["Rank", "Carrier Name", "Reliability", "ETA (hrs)", "Cost (Rs)"]]
        for c in carriers[:3]:
            c_data.append([str(c.get('rank')), c.get('name'), f"{c.get('reliability')}%", str(c.get('eta_hours')), f"{c.get('estimated_cost'):,}"])
        
        t_c = Table(c_data, colWidths=[40, 200, 80, 80, 100])
        t_c.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        elements.append(t_c)
        
    # Emergency Routes
    elements.append(Paragraph("<b>5. Emergency Routes</b>", heading_style))
    routes = data.get("emergency_routes", [])
    if routes:
        r_data = [["Type", "Path", "Risk", "ETA Impact"]]
        for r in routes:
            r_data.append([r.get('type'), r.get('path'), f"{r.get('risk_pct')}%", f"{r.get('eta_impact_hrs')} hrs"])
            
        t_r = Table(r_data, colWidths=[100, 220, 80, 100])
        t_r.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        elements.append(t_r)
        
    # Executive Escalation
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<b>6. Executive Escalation Matrix</b>", heading_style))
    elements.append(Paragraph("<b>VP Logistics:</b> Sarah Jenkins (sarah.j@logispark.com) - +1 555-0192", normal_style))
    elements.append(Paragraph("<b>Director Freight:</b> Michael Chen (m.chen@logispark.com) - +1 555-0193", normal_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
