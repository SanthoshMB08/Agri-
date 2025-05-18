from fpdf import FPDF
from io import BytesIO

def generate_pdf(title, user_input, match_data, ai_suggestion):
    pdf = FPDF()
    pdf.add_page()

    # Add a Unicode TTF font (make sure the TTF file is accessible)
    # Download DejaVuSans.ttf from https://dejavu-fonts.github.io/
    pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
    pdf.add_font('DejaVu', 'B', 'DejaVuSans-Bold.ttf', uni=True)  # Bold font variant

    # Title
    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(200, 10, txt=title, ln=True, align="C")
    pdf.ln(10)

    # User Input
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(200, 10, txt="User Input:", ln=True)
    pdf.set_font("DejaVu", size=12)
    for line in user_input.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf.ln(5)

    # Matching Data
    if match_data:
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(200, 10, txt="Matching Crops/Data:", ln=True)
        pdf.set_font("DejaVu", size=12)
        for line in match_data.split('\n'):
            pdf.multi_cell(0, 10, line)
        pdf.ln(5)

    # AI Suggestion
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(200, 10, txt="AI Suggestion:", ln=True)
    pdf.set_font("DejaVu", size=12)
    for line in ai_suggestion.split('\n'):
        pdf.multi_cell(0, 10, line)

  # Instead of pdf.output(buffer), do this:
    pdf_bytes = pdf.output(dest='S').encode('latin1')  # get PDF as bytes string
    buffer = BytesIO(pdf_bytes)
    buffer.seek(0)
    return buffer
