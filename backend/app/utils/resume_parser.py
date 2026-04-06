import fitz

def extract_text(file_path):
    """
    Extracts text from a PDF while preserving layout by grouping items into lines.
    Handles multi-column layouts by sorting blocks by vertical position first.
    """
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            blocks = page.get_text("blocks")
            
            # Sort all blocks
            blocks.sort(key=lambda b: (b[1], b[0]))
            
            current_y = -1
            line_buffer = []
            
            for b in blocks:
                # b[1] is y0. If it's within 2 units of the last seen y0, it's on the same line.
                if current_y == -1 or abs(b[1] - current_y) < 3:
                    if current_y == -1:
                        current_y = b[1]
                    line_buffer.append(b)
                else:
                    # Sort blocks within the line by x0
                    line_buffer.sort(key=lambda x: x[0])
                    for lb in line_buffer:
                        text += lb[4].strip() + " "
                    text += "\n"
                    
                    # Reset for the new line
                    line_buffer = [b]
                    current_y = b[1]
            
            # Flush the last line
            if line_buffer:
                line_buffer.sort(key=lambda x: x[0])
                for lb in line_buffer:
                    text += lb[4].strip() + " "
                text += "\n"
                    
    return text