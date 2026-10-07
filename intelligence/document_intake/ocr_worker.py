import contextlib
import io
import json
import sys


def extract(content, suffix):
    import numpy as np
    from rapidocr_onnxruntime import RapidOCR
    from intelligence.document_intake.ocr import validate_image

    images, warnings = [], []
    if suffix == ".pdf":
        import pypdfium2 as pdfium

        with pdfium.PdfDocument(content) as document:
            if len(document) > 4:
                warnings.append(
                    "OCR processes the first four pages only; split longer documents and review completeness."
                )
            for index in range(min(4, len(document))):
                page = document[index]
                try:
                    width, height = page.get_size()
                    bitmap = page.render(
                        scale=min(2, (8_000_000 / max(1, width * height)) ** 0.5)
                    )
                    images.append(bitmap.to_pil().convert("RGB").copy())
                    bitmap.close()
                finally:
                    page.close()
    else:
        images = [validate_image(content)]
    engine = RapidOCR(intra_op_num_threads=1, inter_op_num_threads=1)
    lines, scores = [], []
    for image in images:
        result, _ = engine(np.asarray(image))
        for _, text, score in result or []:
            lines.append(text)
            scores.append(float(score))
    return {
        "text": "\n".join(lines)[:30000],
        "source": "local_onnx_ocr",
        "confidence": round(sum(scores) / len(scores), 3) if scores else None,
        "warnings": warnings
        + [
            "OCR recognition confidence is not calibrated cargo-field accuracy; confirm all fields."
        ],
    }


if __name__ == "__main__":
    try:
        content = sys.stdin.buffer.read(8 * 1024 * 1024 + 1)
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            result = extract(content, sys.argv[1])
        sys.stdout.write(json.dumps(result))
    except Exception:
        sys.exit(2)
