import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf_report(shipment_data: dict, output_path: str):
    """
    Generates an enterprise-grade PDF report using ReportLab.
    """
    doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1e3a8a'), spaceAfter=20)
    h2_style = ParagraphStyle('Heading2', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#3b82f6'), spaceBefore=15, spaceAfter=10)
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    normal_style.leading = 14
    
    # Header
    story.append(Paragraph(f"LogiSPARK Decision Support - Delay Report", title_style))
    story.append(Paragraph(f"Shipment ID: <b>{shipment_data['shipment_id']}</b> | Date: 2026-06-17", normal_style))
    story.append(Spacer(1, 15))
    
    # Executive Summary
    story.append(Paragraph("1. AI Executive Summary", h2_style))
    story.append(Paragraph(shipment_data['ai_summary'], normal_style))
    story.append(Spacer(1, 15))
    
    # Delay Classification
    story.append(Paragraph("2. Delay Classification", h2_style))
    clf = shipment_data.get('delay_classification', {})
    clf_data = [
        ["Attribute", "Value"],
        ["Delay Type", clf.get('type', '-')],
        ["Severity", clf.get('severity', '-')],
        ["Predicted Delay Hours", str(shipment_data['predicted_delay_hours'])],
        ["Confidence", f"{clf.get('confidence', 0)}%"]
    ]
    clf_table = Table(clf_data, colWidths=[200, 200])
    clf_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0,0), (1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8fafc')),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
    ]))
    story.append(clf_table)
    story.append(Spacer(1, 15))
    
    # Financial Impact Breakdown
    story.append(Paragraph("3. Financial Impact Breakdown", h2_style))
    fin = shipment_data.get('financial_breakdown', {})
    fin_data = [["Component", "Estimated Loss (INR)"]]
    for k, v in fin.items():
        if k != "total_loss":
            fin_data.append([k.replace("_", " ").title(), f"Rs. {v:,}"])
    fin_data.append(["TOTAL ESTIMATED LOSS", f"Rs. {fin.get('total_loss', 0):,}"])
    
    fin_table = Table(fin_data, colWidths=[250, 150])
    fin_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0,0), (1,0), colors.whitesmoke),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#e2e8f0')),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
    ]))
    story.append(fin_table)
    story.append(Spacer(1, 15))
    
    # Recommendation & Savings
    story.append(Paragraph("4. Recommended Mitigation Strategy", h2_style))
    rec = shipment_data.get('recommendation_v2', {})
    story.append(Paragraph(f"<b>Recommended Action:</b> {rec.get('recommended_action', '-')}", normal_style))
    story.append(Paragraph(f"<b>Reason:</b> {rec.get('reason', '-')}", normal_style))
    story.append(Paragraph(f"<b>Expected Savings:</b> Rs. {rec.get('potential_savings', 0):,}", normal_style))
    story.append(Paragraph(f"<b>Implementation Cost:</b> Rs. {rec.get('implementation_cost', 0):,}", normal_style))
    story.append(Paragraph(f"<b>Net Benefit:</b> Rs. {rec.get('net_benefit', 0):,}", normal_style))
    story.append(Paragraph(f"<b>Risk Reduction:</b> {rec.get('risk_reduction', '-')}", normal_style))
    story.append(Spacer(1, 15))

    # Enterprise ETA Analysis
    if 'eta_analysis' in shipment_data:
        story.append(Paragraph("5. Advanced ETA Analysis", h2_style))
        eta = shipment_data['eta_analysis']
        eta_data = [
            ["Metric", "Value"],
            ["Original ETA", f"{eta.get('original_eta_date')} ({eta.get('original_eta_day')})"],
            ["Predicted ETA", f"{eta.get('predicted_eta_date')} ({eta.get('predicted_eta_day')})"],
            ["Additional Days", str(eta.get('additional_days'))],
            ["On-Time Probability", f"{eta.get('on_time_probability')}%"]
        ]
        eta_table = Table(eta_data, colWidths=[200, 200])
        eta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (1,0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0,0), (1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8fafc')),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ]))
        story.append(eta_table)
        story.append(Spacer(1, 15))

    doc.build(story)
    return output_path
