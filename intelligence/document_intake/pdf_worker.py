import sys
import json
from io import BytesIO
from pypdf import PdfReader

if __name__ == "__main__":
    try:
        content = sys.stdin.buffer.read(8 * 1024 * 1024 + 1)
        reader = PdfReader(BytesIO(content))
        if reader.is_encrypted or len(reader.pages) > 40:
            raise ValueError()
        text = ""
        for page in reader.pages:
            text += (page.extract_text() or "") + "\n"
            if len(text) >= 30000:
                break
        sys.stdout.write(json.dumps({"text": text[:30000]}))
    except Exception:
        sys.exit(2)
