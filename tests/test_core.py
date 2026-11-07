import unittest
from bankassist.core import BankAssistant, Document, ExtractiveGenerator, KeywordRetriever


class AssistantTests(unittest.TestCase):
    def setUp(self):
        self.bot = BankAssistant(KeywordRetriever([Document('P1', 'Report a lost card in the app.')]), ExtractiveGenerator())

    def test_grounded_baseline(self):
        result = self.bot.answer('lost card')
        self.assertEqual(result.sources, ('P1',))
        self.assertIn('[P1]', result.text)

    def test_missing_evidence(self):
        result = self.bot.answer('mortgage interest')
        self.assertEqual(result.sources, ())
        self.assertIn('cannot answer', result.text)

    def test_empty_input(self):
        with self.assertRaises(ValueError):
            self.bot.answer('  ')


if __name__ == '__main__':
    unittest.main()
