import io
import unittest
from unittest.mock import Mock, patch

import requests

from pypdf import PdfWriter
from werkzeug.datastructures import FileStorage

import app as quiz_app
from study_source import extract_source, quote_is_in_source


NOTES = ("Photosynthesis uses light energy to convert carbon dioxide and water into glucose. "
         "Chlorophyll in chloroplasts absorbs light, and oxygen is released as a byproduct. "
         "The light reactions produce ATP and NADPH, which the Calvin cycle uses to fix carbon. ") * 3


def sample_quiz(source=None):
    citation = {'source_ref': 'Section 1',
                'source_quote': 'Photosynthesis uses light energy to convert carbon dioxide and water into glucose.'} if source else {}
    question = {'question': 'What does photosynthesis use?',
                'options': ['Light energy', 'Sound', 'Heat only', 'Nothing'],
                'answer_index': 0, 'explanation': 'It uses light energy.',
                'concept': 'Photosynthesis', 'study_tip': 'Review energy conversion.', **citation}
    return {'summary': 'A quiz on photosynthesis', 'questions': [dict(question) for _ in range(5)],
            'next_topics': []}


class StudyFeaturesTests(unittest.TestCase):
    def setUp(self):
        self.client = quiz_app.app.test_client()

    def test_notes_validation(self):
        upload = lambda name, data: FileStorage(stream=io.BytesIO(data), filename=name)
        source = extract_source(upload('notes.txt', NOTES.encode()))
        self.assertTrue(quote_is_in_source(source, 'Section 1',
                        'Photosynthesis uses light energy to convert carbon dioxide and water into glucose.'))
        self.assertFalse(quote_is_in_source(source, 'Section 2', 'Photosynthesis uses light energy'))
        for name, data, message in [
            ('notes.exe', NOTES.encode(), 'Upload a PDF'),
            ('notes.txt', b'', 'empty'),
            ('notes.txt', b'\xff' * 400, 'UTF-8'),
            ('notes.txt', b'hello\x00' * 100, 'plain text'),
            ('notes.txt', b'A' * (2 * 1024 * 1024 + 1), 'under 2 MB'),
        ]:
            with self.subTest(name=name, message=message):
                with self.assertRaisesRegex(ValueError, message):
                    extract_source(upload(name, data))
        writer = PdfWriter()
        writer.add_blank_page(width=400, height=400)
        output = io.BytesIO()
        writer.write(output)
        with self.assertRaisesRegex(ValueError, 'No selectable text'):
            extract_source(upload('scan.pdf', output.getvalue()))

    def test_source_citation_rejected_when_unverified(self):
        source = extract_source(FileStorage(stream=io.BytesIO(NOTES.encode()), filename='notes.txt'))
        quiz = sample_quiz(source)
        self.assertEqual(len(quiz_app.validate_quiz(quiz, 5, source)['questions']), 5)
        quiz['questions'][0]['source_quote'] = 'An invented fact that never appears in the uploaded notes'
        with self.assertRaisesRegex(ValueError, 'verified note citation'):
            quiz_app.validate_quiz(quiz, 5, source)

    def test_topic_redirect_and_quiz_page(self):
        response = self.client.post('/', data={'topic': 'Space & time', 'count': '5', 'difficulty': 'hard'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/quiz/Space%20&%20time?', response.location)
        with patch.object(quiz_app, 'GOOGLE_API_KEY', 'test'), patch.object(
                quiz_app, 'generate_questions', return_value=(quiz_app.validate_quiz(sample_quiz(), 5), 'test')):
            page = self.client.get(response.location)
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'id="quiz-form"', page.data)
        self.assertIn(b'data-tutor="simple"', page.data)
        self.assertEqual(page.data.count(b'<form'), 1)

    def test_notes_route_success_and_errors(self):
        settings = {'topic': 'Biology', 'count': '5', 'difficulty': 'medium'}
        missing = self.client.post('/notes/quiz', data=settings)
        self.assertEqual(missing.status_code, 400)
        self.assertIn(b'Choose a PDF', missing.data)
        with patch.object(quiz_app, 'GOOGLE_API_KEY', 'test'), patch.object(
                quiz_app, 'generate_source_questions', return_value=(
                    quiz_app.validate_quiz(sample_quiz(True), 5,
                        extract_source(FileStorage(stream=io.BytesIO(NOTES.encode()), filename='notes.txt'))), 'test')):
            page = self.client.post('/notes/quiz', data={**settings,
                'notes_file': (io.BytesIO(NOTES.encode()), 'notes.txt')})
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'Section 1', page.data)
        self.assertIn(b'Reupload notes to practise', page.data)
        self.assertNotIn(b'id="share-link"', page.data)
        too_large = self.client.post('/notes/quiz', data={**settings,
            'notes_file': (io.BytesIO(b'a' * (2 * 1024 * 1024 + 1)), 'notes.txt')})
        self.assertEqual(too_large.status_code, 400)
        self.assertIn(b'under 2 MB', too_large.data)

    def test_tutor_validation_and_reply(self):
        payload = {'mode': 'simple', 'question': 'What uses light?', 'answer': 'Photosynthesis'}
        self.assertEqual(self.client.post('/api/tutor', json=payload,
            headers={'Origin': 'https://elsewhere.example'}).status_code, 403)
        self.assertEqual(self.client.post('/api/tutor', json={**payload, 'mode': 'ask'}).status_code, 400)
        with patch.object(quiz_app, 'GOOGLE_API_KEY', 'test'), patch.object(
                quiz_app, 'call_gemini', return_value=({'reply': 'Plants use light to make food.'}, 'test')):
            response = self.client.post('/api/tutor', json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['reply'], 'Plants use light to make food.')

    def test_model_fallback_after_timeout_and_unavailable_model(self):
        unavailable = Mock(status_code=404)
        success = Mock(status_code=200)
        success.json.return_value = {'candidates': [{'content': {'parts': [{'text': '{"ok": true}'}]}}]}
        with patch.object(quiz_app, 'GOOGLE_API_KEY', 'test'), patch.object(
                quiz_app, 'model_candidates', return_value=['first', 'second', 'third']), patch.object(
                quiz_app.requests, 'post', side_effect=[requests.Timeout(), unavailable, success]) as post:
            response, model = quiz_app.call_gemini('test prompt')
        self.assertEqual(response, {'ok': True})
        self.assertEqual(model, 'third')
        self.assertEqual(post.call_count, 3)


if __name__ == '__main__':
    unittest.main()
