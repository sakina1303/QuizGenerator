"""Extract bounded, cited text from a learner's notes without storing the file."""

from io import BytesIO
import re

from pypdf import PdfReader
from pypdf.errors import PdfReadError


MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_SOURCE_CHARS = 28_000
MAX_PDF_PAGES = 20
MIN_SOURCE_CHARS = 300
ALLOWED_SUFFIXES = {'.pdf', '.txt', '.md'}


def normalize_quote(value):
    return re.sub(r'\s+', ' ', value).strip().casefold()


def extract_source(upload):
    filename = (upload.filename or '').rsplit('/', 1)[-1].rsplit('\\', 1)[-1]
    suffix = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if suffix not in ALLOWED_SUFFIXES:
        raise ValueError('Upload a PDF, .txt, or .md file.')
    content = upload.stream.read(MAX_FILE_BYTES + 1)
    if not content:
        raise ValueError('The notes file is empty.')
    if len(content) > MAX_FILE_BYTES:
        raise ValueError('Keep the notes file under 2 MB.')

    chunks = []
    if suffix == '.pdf':
        if not content.startswith(b'%PDF-'):
            raise ValueError('This is not a valid PDF file.')
        try:
            reader = PdfReader(BytesIO(content), strict=False)
            if reader.is_encrypted:
                raise ValueError('Unlock the PDF before uploading it.')
            if len(reader.pages) > MAX_PDF_PAGES:
                raise ValueError('Upload a PDF of 20 pages or fewer.')
            for index, page in enumerate(reader.pages, 1):
                text = re.sub(r'\s+', ' ', page.extract_text() or '').strip()
                if text:
                    chunks.append({'ref': f'Page {index}', 'text': text})
        except (PdfReadError, OSError, KeyError, TypeError, ValueError) as error:
            if isinstance(error, ValueError):
                raise
            raise ValueError('Could not read this PDF. Try a text-based PDF.') from error
        if not chunks:
            raise ValueError('No selectable text was found in this PDF. Try a text-based PDF or .txt notes.')
    else:
        try:
            text = content.decode('utf-8-sig')
        except UnicodeDecodeError as error:
            raise ValueError('Save the notes as UTF-8 text before uploading.') from error
        if '\x00' in text:
            raise ValueError('This file does not appear to contain plain text.')
        text = re.sub(r'\s+', ' ', text).strip()
        for offset in range(0, len(text), 1600):
            part = text[offset:offset + 1600].strip()
            if part:
                chunks.append({'ref': f'Section {len(chunks) + 1}', 'text': part})

    length = sum(len(chunk['text']) for chunk in chunks)
    if length < MIN_SOURCE_CHARS:
        raise ValueError('Add at least 300 characters of readable notes for a useful quiz.')
    if length > MAX_SOURCE_CHARS:
        raise ValueError('This file has too much text. Use a shorter chapter (up to 28,000 characters).')
    return {'name': filename[:100], 'kind': 'notes', 'chunks': chunks}


def quote_is_in_source(source, reference, quote):
    if not isinstance(reference, str) or not isinstance(quote, str):
        return False
    normalized = normalize_quote(quote)
    if len(normalized) < 20 or len(normalized) > 240:
        return False
    return any(chunk['ref'] == reference and normalized in normalize_quote(chunk['text'])
               for chunk in source['chunks'])
