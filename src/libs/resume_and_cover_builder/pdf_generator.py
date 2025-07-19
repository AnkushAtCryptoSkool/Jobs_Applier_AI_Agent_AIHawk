"""
PDF generation utility using reportlab for converting HTML to PDF.
"""
import os
import re
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, blue
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from html import unescape
from html.parser import HTMLParser


class HTMLToTextParser(HTMLParser):
    """Simple HTML parser to extract text content."""
    
    def __init__(self):
        super().__init__()
        self.text = []
        self.in_title = False
        self.in_heading = False
        self.in_paragraph = False
        self.current_style = None
        
    def handle_starttag(self, tag, attrs):
        if tag.lower() in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.in_heading = True
            self.current_style = 'heading'
        elif tag.lower() == 'title':
            self.in_title = True
        elif tag.lower() == 'p':
            self.in_paragraph = True
            self.current_style = 'paragraph'
        elif tag.lower() == 'strong' or tag.lower() == 'b':
            self.current_style = 'bold'
        elif tag.lower() == 'em' or tag.lower() == 'i':
            self.current_style = 'italic'
        elif tag.lower() == 'br':
            self.text.append('\n')
        elif tag.lower() == 'li':
            self.text.append('• ')
    
    def handle_endtag(self, tag):
        if tag.lower() in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.in_heading = False
            self.text.append('\n\n')
        elif tag.lower() == 'title':
            self.in_title = False
        elif tag.lower() == 'p':
            self.in_paragraph = False
            self.text.append('\n\n')
        elif tag.lower() in ['div', 'section']:
            self.text.append('\n')
        elif tag.lower() == 'li':
            self.text.append('\n')
    
    def handle_data(self, data):
        if self.in_title or self.in_heading or self.in_paragraph:
            cleaned_data = ' '.join(data.split())  # Clean up whitespace
            if cleaned_data:
                self.text.append(cleaned_data)
    
    def get_text(self):
        return ''.join(self.text)


class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for better formatting."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=black,
            alignment=TA_CENTER
        ))
        
        # Heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=12,
            textColor=black,
            alignment=TA_LEFT
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            textColor=black,
            alignment=TA_JUSTIFY
        ))
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text."""
        parser = HTMLToTextParser()
        parser.feed(html_content)
        return parser.get_text()
    
    def _create_pdf_from_text(self, text_content: str, output_path: str):
        """Create PDF from text content."""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Split content into sections
        sections = text_content.split('\n\n')
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
                
            # Check if it's a title/heading (simple heuristic)
            if len(section) < 100 and section.isupper():
                # Likely a title
                story.append(Paragraph(section, self.styles['CustomTitle']))
            elif len(section) < 100 and any(word in section.lower() for word in ['experience', 'education', 'skills', 'contact']):
                # Likely a heading
                story.append(Paragraph(section, self.styles['CustomHeading']))
            else:
                # Regular paragraph
                story.append(Paragraph(section, self.styles['CustomBody']))
            
            story.append(Spacer(1, 6))
        
        doc.build(story)
    
    def html_to_pdf(self, html_content: str, output_path: str, css_content: str = None):
        """
        Convert HTML content to PDF file.
        
        Args:
            html_content (str): HTML content to convert
            output_path (str): Path where PDF will be saved
            css_content (str): Optional CSS content (ignored for now)
        """
        try:
            # Ensure output directory exists
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Convert HTML to text
            text_content = self._html_to_text(html_content)
            
            # Create PDF
            self._create_pdf_from_text(text_content, output_path)
            
            return True
            
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            return False
    
    def save_html_and_pdf(self, html_content: str, base_path: str, css_content: str = None):
        """
        Save both HTML and PDF versions of the document.
        
        Args:
            html_content (str): HTML content to save
            base_path (str): Base path without extension
            css_content (str): Optional CSS content for styling
        
        Returns:
            tuple: (html_path, pdf_path, success)
        """
        html_path = f"{base_path}.html"
        pdf_path = f"{base_path}.pdf"
        
        try:
            # Save HTML file
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Generate PDF
            pdf_success = self.html_to_pdf(html_content, pdf_path, css_content)
            
            return html_path, pdf_path, pdf_success
            
        except Exception as e:
            print(f"Error saving files: {str(e)}")
            return html_path, pdf_path, False 