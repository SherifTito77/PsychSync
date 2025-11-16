

#app/reports/generate_report.py

"""
Report Generation and Data Export for PsychSync
PDF reports, Excel exports, and custom report builder.

Requirements:
    pip install reportlab pandas openpyxl matplotlib
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak, Image as RLImage
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any
import io
import base64


# ============================================================================
# PDF Report Generator
# ============================================================================

class PDFReportGenerator:
    """
    Generate professional PDF reports for clinical and research purposes.
    """
    
    def __init__(self, title: str = "PsychSync Report"):
        """
        Initialize PDF report generator.
        
        Args:
            title: Report title
        """
        self.title = title
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()
    
    def _add_custom_styles(self):
        """Add custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a56db'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6
        ))
    
    def generate_client_progress_report(
        self,
        client_info: Dict,
        assessment_scores: pd.DataFrame,
        session_summary: Dict,
        output_file: str
    ):
        """
        Generate comprehensive client progress report.
        
        Args:
            client_info: Client demographic information
            assessment_scores: DataFrame with assessment scores over time
            session_summary: Summary of sessions
            output_file: Output PDF file path
        """
        doc = SimpleDocTemplate(
            output_file,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Container for report elements
        elements = []
        
        # Title
        elements.append(Paragraph(self.title, self.styles['CustomTitle']))
        elements.append(Spacer(1, 12))
        
        # Report metadata
        report_date = datetime.now().strftime("%B %d, %Y")
        elements.append(Paragraph(f"Report Date: {report_date}", self.styles['BodyText']))
        elements.append(Spacer(1, 20))
        
        # Client Information Section
        elements.append(Paragraph("Client Information", self.styles['SectionHeader']))
        
        client_data = [
            ["Client ID:", client_info.get('client_id', 'N/A')],
            ["Age:", str(client_info.get('age', 'N/A'))],
            ["Gender:", client_info.get('gender', 'N/A')],
            ["Primary Diagnosis:", client_info.get('diagnosis', 'N/A')],
            ["Treatment Start Date:", client_info.get('start_date', 'N/A')]
        ]
        
        client_table = Table(client_data, colWidths=[2*inch, 4*inch])
        client_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e5e7eb')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        elements.append(client_table)
        elements.append(Spacer(1, 20))
        
        # Treatment Summary Section
        elements.append(Paragraph("Treatment Summary", self.styles['SectionHeader']))
        
        summary_data = [
            ["Total Sessions:", str(session_summary.get('total_sessions', 0))],
            ["Sessions Attended:", str(session_summary.get('attended', 0))],
            ["Attendance Rate:", f"{session_summary.get('attendance_rate', 0):.1f}%"],
            ["Homework Completion:", f"{session_summary.get('homework_completion', 0):.1f}%"],
            ["Treatment Duration:", f"{session_summary.get('duration_weeks', 0)} weeks"]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e5e7eb')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Assessment Scores Section
        elements.append(Paragraph("Assessment Scores", self.styles['SectionHeader']))
        
        if not assessment_scores.empty:
            # Create table from DataFrame
            score_data = [assessment_scores.columns.tolist()] + assessment_scores.values.tolist()
            
            score_table = Table(score_data)
            score_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            
            elements.append(score_table)
        else:
            elements.append(Paragraph("No assessment data available.", self.styles['BodyText']))
        
        elements.append(Spacer(1, 20))
        
        # Progress Interpretation
        elements.append(Paragraph("Clinical Progress", self.styles['SectionHeader']))
        
        if not assessment_scores.empty and 'score' in assessment_scores.columns:
            baseline = assessment_scores['score'].iloc[0]
            current = assessment_scores['score'].iloc[-1]
            change = baseline - current
            pct_change = (change / baseline * 100) if baseline > 0 else 0
            
            progress_text = f"""
            Baseline Score: {baseline:.1f}<br/>
            Current Score: {current:.1f}<br/>
            Change: {change:.1f} points ({pct_change:.1f}% improvement)<br/>
            <br/>
            """
            
            if pct_change >= 50:
                progress_text += "Excellent progress. Client has achieved significant symptom reduction."
            elif pct_change >= 25:
                progress_text += "Good progress. Client is responding well to treatment."
            elif pct_change >= 10:
                progress_text += "Moderate progress. Continue current treatment approach."
            else:
                progress_text += "Limited progress. Consider treatment adjustment."
            
            elements.append(Paragraph(progress_text, self.styles['BodyText']))
        
        elements.append(Spacer(1, 20))
        
        # Recommendations
        elements.append(Paragraph("Recommendations", self.styles['SectionHeader']))
        recommendations_text = """
        • Continue weekly therapy sessions<br/>
        • Maintain focus on cognitive restructuring techniques<br/>
        • Monitor symptoms with bi-weekly assessments<br/>
        • Review progress in 4 weeks
        """
        elements.append(Paragraph(recommendations_text, self.styles['BodyText']))
        
        # Footer
        elements.append(Spacer(1, 40))
        footer_text = f"""
        <para align=center>
        <font size=9 color=grey>
        This report is confidential and intended solely for clinical use.<br/>
        Generated by PsychSync on {report_date}
        </font>
        </para>
        """
        elements.append(Paragraph(footer_text, self.styles['Normal']))
        
        # Build PDF
        doc.build(elements)
    
    def generate_outcome_summary_report(
        self,
        summary_stats: Dict,
        clients_data: pd.DataFrame,
        output_file: str
    ):
        """
        Generate outcome summary report for multiple clients.
        
        Args:
            summary_stats: Aggregate statistics
            clients_data: DataFrame with client outcomes
            output_file: Output PDF file path
        """
        doc = SimpleDocTemplate(output_file, pagesize=letter)
        elements = []
        
        # Title
        elements.append(Paragraph("Treatment Outcomes Summary", self.styles['CustomTitle']))
        elements.append(Spacer(1, 20))
        
        # Report period
        report_date = datetime.now().strftime("%B %d, %Y")
        elements.append(Paragraph(f"Report Date: {report_date}", self.styles['BodyText']))
        elements.append(Spacer(1, 20))
        
        # Summary statistics
        elements.append(Paragraph("Overall Statistics", self.styles['SectionHeader']))
        
        stats_data = [
            ["Total Clients:", str(summary_stats.get('total_clients', 0))],
            ["Active Clients:", str(summary_stats.get('active_clients', 0))],
            ["Average Improvement:", f"{summary_stats.get('avg_improvement', 0):.1f}%"],
            ["Recovery Rate:", f"{summary_stats.get('recovery_rate', 0):.1f}%"],
            ["Average Sessions:", f"{summary_stats.get('avg_sessions', 0):.1f}"]
        ]
        
        stats_table = Table(stats_data, colWidths=[2.5*inch, 3.5*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#dbeafe')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        elements.append(stats_table)
        elements.append(Spacer(1, 20))
        
        # Client outcomes table
        if not clients_data.empty:
            elements.append(Paragraph("Client Outcomes", self.styles['SectionHeader']))
            
            # Limit to first 20 clients
            display_data = clients_data.head(20)
            table_data = [display_data.columns.tolist()] + display_data.values.tolist()
            
            outcome_table = Table(table_data)
            outcome_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            
            elements.append(outcome_table)
        
        doc.build(elements)


# ============================================================================
# Excel Export
# ============================================================================

class ExcelExporter:
    """
    Export data to Excel with formatting and multiple sheets.
    """
    
    @staticmethod
    def export_client_data(
        client_info: Dict,
        assessment_data: pd.DataFrame,
        session_data: pd.DataFrame,
        output_file: str
    ):
        """
        Export client data to Excel with multiple sheets.
        
        Args:
            client_info: Client information dictionary
            assessment_data: Assessment scores DataFrame
            session_data: Session records DataFrame
            output_file: Output Excel file path
        """
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Client Info sheet
            client_df = pd.DataFrame([client_info])
            client_df.to_excel(writer, sheet_name='Client Info', index=False)
            
            # Assessment scores
            if not assessment_data.empty:
                assessment_data.to_excel(writer, sheet_name='Assessments', index=False)
            
            # Session records
            if not session_data.empty:
                session_data.to_excel(writer, sheet_name='Sessions', index=False)
            
            # Summary statistics
            if not assessment_data.empty and 'score' in assessment_data.columns:
                summary_data = {
                    'Metric': [
                        'Baseline Score',
                        'Current Score',
                        'Change',
                        'Percent Change',
                        'Total Assessments'
                    ],
                    'Value': [
                        assessment_data['score'].iloc[0],
                        assessment_data['score'].iloc[-1],
                        assessment_data['score'].iloc[0] - assessment_data['score'].iloc[-1],
                        ((assessment_data['score'].iloc[0] - assessment_data['score'].iloc[-1]) / 
                         assessment_data['score'].iloc[0] * 100) if assessment_data['score'].iloc[0] > 0 else 0,
                        len(assessment_data)
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    @staticmethod
    def export_aggregate_data(
        dataframes: Dict[str, pd.DataFrame],
        output_file: str
    ):
        """
        Export multiple DataFrames to different sheets.
        
        Args:
            dataframes: Dictionary of sheet_name -> DataFrame
            output_file: Output Excel file path
        """
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for sheet_name, df in dataframes.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)


# ============================================================================
# CSV Export
# ============================================================================

class CSVExporter:
    """Simple CSV export functionality."""
    
    @staticmethod
    def export_dataframe(df: pd.DataFrame, output_file: str, **kwargs):
        """Export DataFrame to CSV."""
        df.to_csv(output_file, index=False, **kwargs)
    
    @staticmethod
    def export_with_metadata(
        df: pd.DataFrame,
        metadata: Dict,
        output_file: str
    ):
        """Export DataFrame with metadata header."""
        with open(output_file, 'w') as f:
            # Write metadata as comments
            f.write(f"# PsychSync Data Export\n")
            f.write(f"# Export Date: {datetime.now().isoformat()}\n")
            for key, value in metadata.items():
                f.write(f"# {key}: {value}\n")
            f.write("\n")
        
        # Append data
        df.to_csv(output_file, mode='a', index=False)


# ============================================================================
# Report Builder
# ============================================================================

class ReportBuilder:
    """
    Flexible report builder for custom reports.
    """
    
    def __init__(self):
        """Initialize report builder."""
        self.sections = []
    
    def add_section(self, title: str, content: Any, section_type: str = "text"):
        """
        Add section to report.
        
        Args:
            title: Section title
            content: Section content (text, table, chart)
            section_type: Type of content ('text', 'table', 'chart')
        """
        self.sections.append({
            'title': title,
            'content': content,
            'type': section_type
        })
    
    def generate_report(self, output_file: str, format: str = "pdf"):
        """
        Generate report in specified format.
        
        Args:
            output_file: Output file path
            format: Output format ('pdf', 'excel', 'html')
        """
        if format == "pdf":
            self._generate_pdf(output_file)
        elif format == "excel":
            self._generate_excel(output_file)
        elif format == "html":
            self._generate_html(output_file)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_pdf(self, output_file: str):
        """Generate PDF report."""
        doc = SimpleDocTemplate(output_file, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        for section in self.sections:
            # Add title
            elements.append(Paragraph(section['title'], styles['Heading2']))
            elements.append(Spacer(1, 12))
            
            # Add content based on type
            if section['type'] == 'text':
                elements.append(Paragraph(str(section['content']), styles['Normal']))
            elif section['type'] == 'table' and isinstance(section['content'], pd.DataFrame):
                df = section['content']
                table_data = [df.columns.tolist()] + df.values.tolist()
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
                ]))
                elements.append(table)
            
            elements.append(Spacer(1, 20))
        
        doc.build(elements)
    
    def _generate_excel(self, output_file: str):
        """Generate Excel report."""
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for i, section in enumerate(self.sections):
                sheet_name = section['title'][:31]  # Excel sheet name limit
                
                if section['type'] == 'table' and isinstance(section['content'], pd.DataFrame):
                    section['content'].to_excel(writer, sheet_name=sheet_name, index=False)
                else:
                    # Convert to DataFrame
                    df = pd.DataFrame({'Content': [str(section['content'])]})
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    def _generate_html(self, output_file: str):
        """Generate HTML report."""
        html = "<html><head><title>PsychSync Report</title>"
        html += "<style>body{font-family:Arial,sans-serif;margin:20px;}</style></head><body>"
        
        for section in self.sections:
            html += f"<h2>{section['title']}</h2>"
            
            if section['type'] == 'table' and isinstance(section['content'], pd.DataFrame):
                html += section['content'].to_html(index=False)
            else:
                html += f"<p>{section['content']}</p>"
        
        html += "</body></html>"
        
        with open(output_file, 'w') as f:
            f.write(html)


# Example usage
if __name__ == "__main__":
    print("Report Generation Demo")
    print("=" * 60)
    
    # Sample data
    client_info = {
        'client_id': 'C001',
        'age': 35,
        'gender': 'Female',
        'diagnosis': 'Major Depressive Disorder (F32.1)',
        'start_date': '2024-01-15'
    }
    
    assessment_scores = pd.DataFrame({
        'date': pd.date_range('2024-01-15', periods=10, freq='W'),
        'phq9_score': [18, 17, 15, 14, 12, 11, 10, 9, 8, 7],
        'gad7_score': [15, 14, 13, 12, 10, 9, 8, 7, 6, 5]
    })
    assessment_scores['date'] = assessment_scores['date'].dt.strftime('%Y-%m-%d')
    
    session_summary = {
        'total_sessions': 10,
        'attended': 9,
        'attendance_rate': 90.0,
        'homework_completion': 85.0,
        'duration_weeks': 10
    }
    
    # 1. Generate PDF Report
    print("\n1. Generating PDF Report...")
    pdf_generator = PDFReportGenerator(title="Client Progress Report")
    
    try:
        pdf_generator.generate_client_progress_report(
            client_info,
            assessment_scores,
            session_summary,
            'client_progress_report.pdf'
        )
        print("   ✓ PDF report generated: client_progress_report.pdf")
    except Exception as e:
        print(f"   ✗ Error generating PDF: {e}")
    
    # 2. Export to Excel
    print("\n2. Exporting to Excel...")
    session_data = pd.DataFrame({
        'session_number': range(1, 11),
        'date': pd.date_range('2024-01-15', periods=10, freq='W').strftime('%Y-%m-%d'),
        'attended': [True] * 9 + [False],
        'homework_completed': [True, True, False, True, True, True, True, True, True, False]
    })
    
    try:
        ExcelExporter.export_client_data(
            client_info,
            assessment_scores,
            session_data,
            'client_data_export.xlsx'
        )
        print("   ✓ Excel export completed: client_data_export.xlsx")
    except Exception as e:
        print(f"   ✗ Error exporting Excel: {e}")
    
    # 3. Export to CSV
    print("\n3. Exporting to CSV...")
    try:
        metadata = {
            'export_type': 'assessment_scores',
            'client_id': 'C001',
            'records': len(assessment_scores)
        }
        CSVExporter.export_with_metadata(
            assessment_scores,
            metadata,
            'assessment_scores.csv'
        )
        print("   ✓ CSV export completed: assessment_scores.csv")
    except Exception as e:
        print(f"   ✗ Error exporting CSV: {e}")
    
    # 4. Custom Report Builder
    print("\n4. Building Custom Report...")
    builder = ReportBuilder()
    builder.add_section("Client Overview", f"Client ID: {client_info['client_id']}, Age: {client_info['age']}", "text")
    builder.add_section("Assessment Scores", assessment_scores, "table")
    builder.add_section("Summary", f"Total sessions: {session_summary['total_sessions']}, Attendance: {session_summary['attendance_rate']}%", "text")
    
    try:
        builder.generate_report('custom_report.pdf', format='pdf')
        print("   ✓ Custom PDF report generated: custom_report.pdf")
    except Exception as e:
        print(f"   ✗ Error generating custom report: {e}")
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("\nGenerated files:")
    print("  - client_progress_report.pdf")
    print("  - client_data_export.xlsx")
    print("  - assessment_scores.csv")
    print("  - custom_report.pdf")